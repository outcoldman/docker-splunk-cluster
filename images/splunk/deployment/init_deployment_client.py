import os
import socket


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
        "@DEPLOYMENT_PASS_4_SYMM_KEY@": os.environ.get("INIT_DEPLOYMENT_PASS_4_SYMM_KEY", "deployment-changeme"),
        "@DEPLOYMENT_CLIENT_NAME@": os.environ.get("INIT_DEPLOYMENT_CLIENT_NAME", socket.getfqdn()),
        "@DEPLOYMENT_CLIENT_DEPLOYMENT_SERVER@": os.environ.get("INIT_DEPLOYMENT_CLIENT_DEPLOYMENT_SERVER", "deployment-server:8089")
    }
