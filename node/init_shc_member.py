import os

import init_helpers


def substitution():
    return {
        "@GENERAL_PASS_4_SYMM_KEY@": "example_general_secret",
        "@CLUSTERING_PASS_4_SYMM_KEY@": "example_cluster_secret",
        "@CLUSTERING_CLUSTER_MASTER@": "https://cluster-master:8089",
        "@LICENSE_MASTER@": "https://cluster-master:8089",
        "@SHCLUSTERING_PASS_4_SYMM_KEY@": "example_shc_secret",
        "@SHCLUSTERING_SHCDEPLOYER@": "https://cluster-master:8089",
        "@SHCLUSTERING_MGMT_URI@": "https://%s:8089" % os.environ['HOSTNAME'],
        "@SHCLUSTERING_REPLICATION_FACTOR": os.environ.get("INIT_SHC_REPLICATION_FACTOR", "3"),
        "@INDEX_DISCOVERY_MASTER_URI@": "https://cluster-master:8089",
        "@INDEX_DISCOVERY_PASS_4_SYMM_KEY@": "example_index_discovery_secret"
    }


def before_start():
    init_helpers.wait_dependency("https://cluster-master:8089", "cluster_master")
