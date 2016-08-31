import os

import init_helpers


def configurations():
    return {
        "components": {
            "kvstore": False,
            "web": False,
            "indexing": False,
            "dmc": False
        }
    }


def substitution():
    return {
        "@SHCLUSTERING_PASS_4_SYMM_KEY@": os.environ.get("INIT_SHCLUSTERING_PASS_4_SYMM_KEY", "shclustering-changeme"),
        "@SHCLUSTERING_SHCLUSTER_LABEL@": os.environ.get("INIT_SHCLUSTERING_SHCLUSTER_LABEL", "shcluster")
    }
