import os

import init_helpers


print "Initializing " + os.environ['HOSTNAME'] + " as SHC Member"

init_helpers.wait_dependency("https://cluster-master:8089", "cluster_master")

init_helpers.splunk_stop()

init_helpers.copy_etc_tree(
    os.path.join("/opt", "splunk-deployment", "shc-member", "etc"),
    os.path.join(os.environ['SPLUNK_HOME'], "etc"),
    {
        "@GENERAL_PASS_4_SYMM_KEY@": "example_general_secret",
        "@CLUSTERING_PASS_4_SYMM_KEY@": "example_cluster_secret",
        "@CLUSTERING_CLUSTER_MASTER@": "https://cluster-master:8089",
        "@LICENSE_MASTER@": "https://cluster-master:8089",
        "@SHCLUSTERING_PASS_4_SYMM_KEY@": "example_shc_secret",
        "@SHCLUSTERING_SHCDEPLOYER@": "https://cluster-master:8089",
        "@SHCLUSTERING_MGMT_URI@": "https://%s:8089" % os.environ['HOSTNAME'],
        "@SHCLUSTERING_REPLICATION_FACTOR": os.environ.get("INIT_SHC_REPLICATION_FACTOR", "3")
    })

init_helpers.splunk_start()

print "Initialized " + os.environ['HOSTNAME'] + " as SHC Member"
print "If this is the first time you setup SHC you need to bootstrap a captain"
print "splunk bootstrap shcluster-captain -auth admin:changeme -servers_list \"...\""
print "or add this member to existing cluster"
print "splunk add shcluster-member -new_member_uri https://" + os.environ['HOSTNAME'] + ":8089"