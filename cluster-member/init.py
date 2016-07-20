import os
import subprocess
import sys
import time

import splunk.clilib.cli_common

import requests

print "Initializing " + os.environ['HOSTNAME'] + " as Cluster Member"

def wait_for_cluster_master():
    """
    At first let's wait for the Cluster Master (wait maximum for 5 minutes)
    """
    for x in xrange(1, 300):
        try:
            # This url does not require authentication, ignore certificate
            response = requests.get("https://cluster-master:8089/services/server/info?output_mode=json", verify=False)
            if response.status_code == 200:
                server_roles = response.json()["entry"][0]["content"]["server_roles"]
                if "cluster_master" in server_roles:
                    return
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)


wait_for_cluster_master()

splunk_bin = os.path.join(os.environ['SPLUNK_HOME'], "bin", "splunk")

sys.stdout.flush()
sys.stderr.flush()

# Initialize Splunk as Cluster Slave
subprocess.check_call(
    [
        splunk_bin,
        "edit",
        "cluster-config",
        "-auth", "admin:changeme",
        "-mode", "slave",
        "-replication_port", "9888",
        "-master_uri", "https://cluster-master:8089",
        "-secret", "example_cluster_secret",
    ]
)

sys.stdout.flush()
sys.stderr.flush()

server_conf_file = os.path.join(os.environ['SPLUNK_HOME'], "etc", "system", "local", "server.conf")
server_conf = splunk.clilib.cli_common.readConfFile(server_conf_file)

# Set general secret on each SHC/IDXC node to use license master
general_stanza = server_conf.setdefault("general", {})
general_stanza["pass4SymmKey"] = "example_general_secret"

# KVStore is only for SH
kvstore_stanza = server_conf.setdefault("kvstore", {})
kvstore_stanza["disabled"] = "true"

splunk.clilib.cli_common.writeConfFile(server_conf_file, server_conf)

# No need to keep web server on indexers
subprocess.check_call(
    [
        splunk_bin,
        "disable",
        "webserver"
    ])

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

sys.stdout.flush()
sys.stderr.flush()

# Initialize as local slave (should be configurable)
subprocess.check_call(
    [
        splunk_bin,
        "edit",
        "licenser-localslave",
        "-master_uri", "https://cluster-master:8089",
        "-auth", "admin:changeme"
    ])

sys.stdout.flush()
sys.stderr.flush()

subprocess.check_call(
    [
        splunk_bin,
        "restart"
    ])

print "Initialized " + os.environ['HOSTNAME'] + " as Cluster Member"