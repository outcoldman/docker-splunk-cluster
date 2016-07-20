import os

import init_helpers

print "Initializing " + os.environ['HOSTNAME'] + " as Cluster Member"

init_helpers.wait_dependency("https://cluster-master:8089", "cluster_master")

init_helpers.splunk_stop()

init_helpers.copy_etc_tree(
    os.path.join("/opt", "splunk-deployment", "cluster-slave", "etc"),
    os.path.join(os.environ['SPLUNK_HOME'], "etc"),
    {
        "@GENERAL_PASS_4_SYMM_KEY@": "example_general_secret",
        "@CLUSTERING_PASS_4_SYMM_KEY@": "example_cluster_secret",
        "@CLUSTERING_CLUSTER_MASTER@": "https://cluster-master:8089",
        "@LICENSE_MASTER@": "https://cluster-master:8089"
    })

init_helpers.splunk_clean_kvstore()

init_helpers.splunk_start()

print "Initialized " + os.environ['HOSTNAME'] + " as Cluster Member"