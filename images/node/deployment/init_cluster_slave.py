import os

import init_helpers


def configurations():
    return {
        "components": {
            "kvstore": False,
            "web": False,
            "indexing": True,
            "dmc": False
        },
        "dependencies": [
            (os.environ.get("INIT_CLUSTERING_CLUSTER_MASTER", "https://cluster-master:8089"), "cluster_master")
        ]
    }


def substitution():
    return {
        "@CLUSTERING_PASS_4_SYMM_KEY@": os.environ.get("INIT_CLUSTERING_PASS_4_SYMM_KEY", "clustering-changeme"),
        "@CLUSTERING_CLUSTER_MASTER@": os.environ.get("INIT_CLUSTERING_CLUSTER_MASTER", "https://cluster-master:8089")
    }
