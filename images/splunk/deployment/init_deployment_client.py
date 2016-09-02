import os
import socket


def substitution():
    return {
        "@DEPLOYMENT_PASS_4_SYMM_KEY@": os.environ.get("INIT_DEPLOYMENT_PASS_4_SYMM_KEY", "deployment-changeme"),
        "@DEPLOYMENT_CLIENT_NAME@": os.environ.get("INIT_DEPLOYMENT_CLIENT_NAME", socket.getfqdn()),
        "@DEPLOYMENT_CLIENT_DEPLOYMENT_SERVER@": os.environ.get("INIT_DEPLOYMENT_CLIENT_DEPLOYMENT_SERVER", "deployment-server:8089")
    }
