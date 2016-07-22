import os

import init_helpers


def configurations():
    return {
        "components": {
            "kvstore": False,
            "web": False,
            "indexing": False
        },
        # shc_deployer will be set only after first deploy, so do not depend on this role
        "dependencies": [
            (os.environ.get("INIT_SHCLUSTERING_SHCDEPLOYER", "https://shc-deployer:8089"), "")
        ]
    }


def substitution():
    return {
        "@SHCLUSTERING_SHCDEPLOYER@": os.environ.get("INIT_SHCLUSTERING_SHCDEPLOYER", "https://shc-deployer:8089")
    }

