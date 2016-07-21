import os

import requests

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


def after_start():
    auto_bootstrap = splunk.util.normalizeBoolean(os.environ.get("INIT_AUTO_BOOTSTRAP_SHC", "false"))
    if auto_bootstrap:
        shc_deployer = os.environ.get("INIT_AUTO_BOOTSTRAP_SHC_DEPLOYER_HANDLER", "http://shc-deployer:8080")
        for x in xrange(1, 300):
            print "sending to " + shc_deployer
            try:
                response = requests.post(shc_deployer, params={"member_uri": get_shc_member_uri()})
                if response.status_code == 200:
                    members = response.json()
                    if members:
                        print "Bootstrapping with '" + ",".join(members) + "'."
                        init_helpers.splunk_execute([
                            "bootstrap",
                            "shcluster-captain",
                            "-auth", "admin:changeme",
                            "-servers_list", ",".join(members)
                        ])
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        print "Failed to post to " + auto_bootstrap_shc
        exit(1)