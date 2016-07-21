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


def configurations():
    return {
        "components": {
            "kvstore": False,
            "web": True,
            "indexing": False
        }
    }


def substitution():
    return {
        "@GENERAL_PASS_4_SYMM_KEY@": os.environ.get("INIT_GENERAL_PASS_4_SYMM_KEY", "general-changeme")
    }
