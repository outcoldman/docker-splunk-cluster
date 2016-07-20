import os
import glob

import init_helpers


def before_stop():
    # Automatically add license
    licenses = glob.glob("/opt/splunk-deployment/*.lic")
    if licenses:
        args = [
            "add",
            "licenses",
            "-auth", "admin:changeme"
        ]
        args.extend(licenses)
        init_helpers.splunk_execute(args)


def substitution():
    return {
        "@GENERAL_PASS_4_SYMM_KEY@": "example_general_secret",
        "@CLUSTERING_PASS_4_SYMM_KEY@": "example_cluster_secret",
        "@CLUSTERING_REPLICATION_FACTOR@": "1",
        "@CLUSTERING_SEARCH_FACTOR@": "1",
        "@INDEX_DISCOVERY_PASS_4_SYMM_KEY@": "example_index_discovery_secret",
        "@SHCLUSTERING_PASS_4_SYMM_KEY@": "example_shc_secret"
    }


def before_start():
    init_helpers.splunk_clean_kvstore()
