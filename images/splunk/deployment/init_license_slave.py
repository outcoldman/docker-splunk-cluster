import os

import init_helpers


def configurations():
    return {
        "components": {
            "kvstore": False,
            "web": False,
            "indexing": False,
            "dmc": False
        },
        "dependencies": [
            ("https://license-master:8089", "license_master")
        ]
    }


def substitution():
    return {
        "@GENERAL_PASS_4_SYMM_KEY@": os.environ.get("INIT_GENERAL_PASS_4_SYMM_KEY", "general-changeme"),
        "@LICENSE_MASTER@": os.environ.get("INIT_LICENSE_MASTER", "https://license-master:8089")
    }
