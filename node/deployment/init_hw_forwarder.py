import os

import init_helpers
import init_consul

import splunk.clilib.cli_common


def configurations():
    return {
        "components": {
            "kvstore": False,
            "web": False,
            "indexing": False
        },
        "dependencies": [
            ("https://cluster-master:8089", "cluster_master")
        ]
    }


def before_start():
    udp_port = os.environ.get("INIT_ADD_UDP_PORT")
    if udp_port:
        inputs_conf = os.path.join(os.environ["SPLUNK_HOME"], "etc", "system", "local", "inputs.conf")
        conf = splunk.clilib.cli_common.readConfFile(inputs_conf) if os.path.exists(inputs_conf) else {}
        conf["udp://" + udp_port] = {
            "connection_host": "dns",
            "index": "splunkcluster"
        }
        splunk.clilib.cli_common.writeConfFile(inputs_conf, conf)


def after_start():
    udp_port = os.environ.get("INIT_ADD_UDP_PORT")
    if udp_port:
        init_consul.register_service({
            "Name": "syslog",
            "Tags": ["splunk", "udp"],
            "Port": int(udp_port)
        })