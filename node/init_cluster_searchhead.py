import os

import init_helpers


def configurations():
    return {
        "components": {
            "kvstore": True,
            "web": True,
            "indexing": False
        },
        "dependencies": [
            ("https://cluster-master:8089", "cluster_master")
        ]
    }


def substitution():
    return {
        "@CLUSTERING_PASS_4_SYMM_KEY@": "example_cluster_secret",
        "@CLUSTERING_CLUSTER_MASTER@": "https://cluster-master:8089",
    }
