import os

import init_helpers


def substitution():
    return {
        "@CLUSTERING_PASS_4_SYMM_KEY@": os.environ.get("INIT_CLUSTERING_PASS_4_SYMM_KEY", "clustering-changeme"),
        "@CLUSTERING_REPLICATION_FACTOR@": os.environ.get("INIT_CLUSTERING_REPLICATION_FACTOR", "1"),
        "@CLUSTERING_SEARCH_FACTOR@": os.environ.get("INIT_CLUSTERING_SEARCH_FACTOR", "1"),
        "@CLUSTERING_CLUSTER_LABEL@": os.environ.get("INIT_CLUSTERING_CLUSTER_LABEL", "cluster"),
        "@INDEX_DISCOVERY_PASS_4_SYMM_KEY@": os.environ.get("INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY", "indexdiscovery-changeme")
    }
