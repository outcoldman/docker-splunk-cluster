import os
import glob
import time

import init_helpers

import splunk.util


def before_stop():
    # Automatically add license
    add_licenses()


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
        "@GENERAL_PASS_4_SYMM_KEY@": os.environ.get("INIT_GENERAL_PASS_4_SYMM_KEY", "general-changeme")
    }


def add_licenses():
    while True:
        if os.path.isdir(os.path.join("/opt", "splunk-deployment", "licenses")):
            licenses = glob.glob(os.path.join("/opt", "splunk-deployment", "licenses", "*.lic"))
            if licenses:
                args = [
                    "add",
                    "licenses",
                    "-auth", "admin:changeme"
                ]
                args.extend(licenses)
                init_helpers.splunk_execute(args)
                break

        if splunk.util.normalizeBoolean(os.environ.get("INIT_WAIT_LICENSE", "False")):
            print "Waiting for license files under /opt/splunk-deployment/licenses/"
            time.sleep(1)
        else:
            break