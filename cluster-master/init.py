import os
import subprocess
import sys
import shutil
import errno
import glob

import splunk.clilib.cli_common

def mkdir_p(path):
    """
    mkdir -p implementation, ref http://stackoverflow.com/a/600612/421143
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


print "Initializing " + os.environ['HOSTNAME'] + " as Cluster Master"

splunk_bin = os.path.join(os.environ['SPLUNK_HOME'], "bin", "splunk")

# Automatically add license
licenses = glob.glob("/opt/splunk-deployment/*.lic")
if licenses:
    args = [
        splunk_bin,
        "add",
        "licenses",
        "-auth", "admin:changeme"
    ]
    args.extend(licenses)
    subprocess.check_call(args)

sys.stdout.flush()
sys.stderr.flush()

# Initialize Splunk as Cluster Master
subprocess.check_call(
    [
        splunk_bin,
        "edit",
        "cluster-config",
        "-auth", "admin:changeme",
        "-mode", "master",
        "-replication_factor", os.environ.get("INIT_CLUSTER_REPLICATION_FACTOR", 4),
        "-search_factor", os.environ.get("INIT_CLUSTER_SEARCH_FACTOR", 3),
        "-secret", "example_cluster_secret"
    ]
)

sys.stdout.flush()
sys.stderr.flush()

# Set general secret on each SHC/IDXC node to use license master
server_conf_file = os.path.join(os.environ['SPLUNK_HOME'], "etc", "system", "local", "server.conf")
server_conf = splunk.clilib.cli_common.readConfFile(server_conf_file)
general_stanza = server_conf.setdefault("general", {})
general_stanza["pass4SymmKey"] = "example_general_secret"

# KVStore is only for SH
kvstore_stanza = server_conf.setdefault("kvstore", {})
kvstore_stanza["disabled"] = "true"

# Generate a passkey for indexer_discovery . This passkey will be specified in the outputs.conf and
# will be used to communicate with master for indexer_discovery
# Set general secret on each SHC/IDXC node to use license master
indexer_discovery_stanza = server_conf.setdefault("indexer_discovery", {})
indexer_discovery_stanza["pass4SymmKey"] = "example_index_discovery_secret"

# Configure cluster master server as shc deployer
shclustering_stanza = server_conf.setdefault("shclustering", {})
shclustering_stanza["pass4SymmKey"] = "example_shc_secret"

splunk.clilib.cli_common.writeConfFile(server_conf_file, server_conf)

mkdir_p(os.path.join(os.environ['SPLUNK_HOME'], "etc", "master-apps"))

shutil.copytree(
    os.path.join("/opt", "splunk-deployment", "etc", "master-apps", "cluster_deployment"),
    os.path.join(os.environ['SPLUNK_HOME'], "etc", "master-apps", "cluster_deployment"))

mkdir_p(os.path.join(os.environ['SPLUNK_HOME'], "etc", "shcluster", "apps"))

shutil.copytree(
    os.path.join("/opt", "splunk-deployment", "etc", "shcluster", "apps", "cluster_deployment"),
    os.path.join(os.environ['SPLUNK_HOME'], "etc", "shcluster", "apps", "cluster_deployment"))

sys.stdout.flush()
sys.stderr.flush()

# Stop
subprocess.check_call(
    [
        splunk_bin,
        "stop"
    ])

sys.stdout.flush()
sys.stderr.flush()

# Clean KVStore as we are not using it on this node
subprocess.check_call(
    [
        splunk_bin,
        "clean",
        "kvstore",
        "-local",
        "-f"
    ])

sys.stdout.flush()
sys.stderr.flush()

subprocess.check_call(
    [
        splunk_bin,
        "start"
    ])

print "Initialized " + os.environ['HOSTNAME'] + " as Cluster Master"