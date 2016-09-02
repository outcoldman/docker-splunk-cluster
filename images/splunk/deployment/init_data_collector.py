import os

import init_helpers
import init_consul

import splunk.util
import splunk.clilib.cli_common


def configurations():
    return {
        "components": {
            "kvstore": False,
            "web": False,
            "indexing": False,
            "dmc": False
        }
    }


def before_start():
    udp_port = os.environ.get("INIT_ADD_UDP_PORT")
    if udp_port:
        inputs_conf = os.path.join(os.environ["SPLUNK_HOME"], "etc", "system", "local", "inputs.conf")
        conf = splunk.clilib.cli_common.readConfFile(inputs_conf) if os.path.exists(inputs_conf) else {}
        conf["udp://" + udp_port] = {
            "connection_host": "dns",
            "index": os.environ.get("INIT_ADD_UDP_PORT_INDEX", "splunkcluster")
        }
        init_helpers.write_conf_file(inputs_conf, conf)


def after_start():
    udp_port = os.environ.get("INIT_ADD_UDP_PORT")
    if udp_port:
        init_consul.register_service({
            "Name": "syslog",
            "Tags": ["splunk", "udp"],
            "Port": int(udp_port)
        })
    public_hec = splunk.util.normalizeBoolean(os.environ.get("INIT_REGISTER_PUBLIC_HTTP_EVENT_COLLECTOR", False))
    if public_hec:
        init_consul.register_service({
            "Name": "http_event_collector",
            "Port": 8088,
            "Tags": ["public"]
        })