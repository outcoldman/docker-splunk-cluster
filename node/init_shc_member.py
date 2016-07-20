import os

import init_helpers


def configurations():
    return {
        "components": {
            "kvstore": True,
            "web": True,
            "indexing": False
        }
    }


def substitution():
    return {
        "@SHCLUSTERING_PASS_4_SYMM_KEY@": "example_shc_secret",
        "@SHCLUSTERING_SHCDEPLOYER@": "https://cluster-master:8089",
        "@SHCLUSTERING_MGMT_URI@": "https://%s:8089" % os.environ['HOSTNAME'],
        "@SHCLUSTERING_REPLICATION_FACTOR": os.environ.get("INIT_SHC_REPLICATION_FACTOR", "3"),
    }
