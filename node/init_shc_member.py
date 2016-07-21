import os
import cherrypy

import splunk.util

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
        "@SHCLUSTERING_PASS_4_SYMM_KEY@": os.environ.get("INIT_SHCLUSTERING_PASS_4_SYMM_KEY", "shclustering-changeme"),
        "@SHCLUSTERING_MGMT_URI@": os.environ.get("INIT_SHCLUSTERING_MGMT_URI", "https://%s:8089" % os.environ['HOSTNAME']),
        "@SHCLUSTERING_REPLICATION_FACTOR@": os.environ.get("INIT_SHCLUSTERING_REPLICATION_FACTOR", "3"),
        "@SHCLUSTERING_SHCLUSTER_LABEL@": os.environ.get("INIT_SHCLUSTERING_SHCLUSTER_LABEL", "shcluster1")
    }
