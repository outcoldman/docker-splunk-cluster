import os

import init_helpers


def substitution():
    return {
        "@GENERAL_PASS_4_SYMM_KEY@": "example_general_secret",
        "@CLUSTERING_PASS_4_SYMM_KEY@": "example_cluster_secret",
        "@CLUSTERING_CLUSTER_MASTER@": "https://cluster-master:8089",
        "@LICENSE_MASTER@": "https://cluster-master:8089"
    }


def before_start():
    init_helpers.splunk_clean_kvstore()
    init_helpers.wait_dependency("https://cluster-master:8089", "cluster_master")
