import os

import splunk.util

import init_consul
import init_helpers


def configurations():
    return {
        "components": {
            "kvstore": False,
            "web": True,
            "indexing": False,
            "dmc": False
        }
    }


def substitution():
    return {
        "@DEPLOYMENT_PASS_4_SYMM_KEY@": os.environ.get("INIT_DEPLOYMENT_PASS_4_SYMM_KEY", "deployment-changeme"),
        "@DEPLOYMENT_REQUIRE_AUTHENTICATION@": os.environ.get("INIT_DEPLOYMENT_REQUIRE_AUTHENTICATION", "false"),
        "@DEPLOYMENT_CROSS_SERVER_CHECKSUM@": os.environ.get("INIT_DEPLOYMENT_CROSS_SERVER_CHECKSUM", "false"),
        "@INPUTS_HTTP_USE_DEPLOYMENT_SERVER@": os.environ.get("INIT_ENABLE_HTTP_EVENT_COLLECTOR", "true")
    }


def before_start():
    if splunk.util.normalizeBoolean(os.environ.get("INIT_ENABLE_HTTP_EVENT_COLLECTOR", "true")):
        init_helpers.copy_etc_tree(
            os.path.join(os.environ['SPLUNK_HOME'], "etc", "apps", "splunk_httpinput"),
            os.path.join(os.environ['SPLUNK_HOME'], "etc", "deployment-apps", "splunk_httpinput")
        )

        serverclass_conf = os.path.join(os.environ["SPLUNK_HOME"], "etc", "system", "local", "serverclass.conf")
        conf = splunk.clilib.cli_common.readConfFile(serverclass_conf) if os.path.exists(serverclass_conf) else {}
        conf["serverClass:data-collector-hec:app:splunk_httpinput"] = {
            "restartSplunkd": True,
            "stateOnClient": "enabled"
        }
        conf["serverClass:data-collector-hec"] = {
            "whitelist.0": os.environ.get("INIT_SERVERCLASS_HTTP_EVENT_COLLECTOR", "data-collector-hec")
        }
        splunk.clilib.cli_common.writeConfFile(serverclass_conf, conf)

        splunk_httpinput_local = os.path.join(os.environ["SPLUNK_HOME"], "etc", "deployment-apps", "splunk_httpinput", "local")
        splunk_httpinput_inputs_conf = os.path.join(splunk_httpinput_local, "inputs.conf")
        conf = splunk.clilib.cli_common.readConfFile(splunk_httpinput_inputs_conf) if os.path.exists(splunk_httpinput_inputs_conf) else {}
        conf["http"] = {
            "disabled": False,
            "useDeploymentServer": False
        }

        if "INIT_HTTP_EVENT_COLLECTOR_TOKEN" in os.environ:
            conf["http://" + os.environ.get("INIT_HTTP_EVENT_COLLECTOR_TOKEN_NAME", "default")] = {
                "disabled": False,
                "token": os.environ["INIT_HTTP_EVENT_COLLECTOR_TOKEN"]
            }

        init_helpers.mkdir_p(splunk_httpinput_local)
        splunk.clilib.cli_common.writeConfFile(splunk_httpinput_inputs_conf, conf)


def after_start():
    deployment_server_tags = ["private"]

    if splunk.util.normalizeBoolean(os.environ.get("INIT_DEPLOYMENT_SERVER_PUBLIC", "false")):
        deployment_server_tags.append("public")

    init_consul.register_service({
        "Name": "DeploymentServer",
        "Port": 8089,
        "Tags": deployment_server_tags
    })
