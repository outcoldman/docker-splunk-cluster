import os

import init_helpers


def configurations():
    return {
        "components": {
            "kvstore": False,
            "web": False,
            "indexing": False
        },
        "dependencies": [
            ("https://license-master:8089", "license_master")
        ]
    }


def substitution():
    return {
        "@GENERAL_PASS_4_SYMM_KEY@": "example_general_secret",
        "@LICENSE_MASTER@": "https://license-master:8089"
    }
