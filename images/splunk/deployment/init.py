import os
import sys
import socket

import init_helpers
import init_consul
import init_cluster_slave
import init_cluster_master
import init_cluster_searchhead
import init_shc_member
import init_license_master
import init_license_slave
import init_shc_deployer
import init_shc_deployer_client
import init_data_collector
import init_deployment_server
import init_deployment_client

import splunk.util


modules = {
    "CLUSTER_SLAVE": init_cluster_slave,
    "CLUSTER_MASTER": init_cluster_master,
    "CLUSTER_SEARCHHEAD": init_cluster_searchhead,
    "SHC_MEMBER": init_shc_member,
    "LICENSE_MASTER": init_license_master,
    "LICENSE_SLAVE": init_license_slave,
    "SHC_DEPLOYER": init_shc_deployer,
    "SHC_DEPLOYER_CLIENT": init_shc_deployer_client,
    "DATA_COLLECTOR": init_data_collector,
    "DEPLOYMENT_SERVER": init_deployment_server,
    "DEPLOYMENT_CLIENT": init_deployment_client
}


def main():
    """
    Initialize node
    """
    roles = [role.upper() for role in os.environ.get("SPLUNK_ROLES", "").split(",")]
    dependencies = []
    for role in roles:
        module = modules.get(role.upper())
        configurations = module.configurations() if hasattr(module, "configurations") else {}
        dependencies.extend(configurations.get("dependencies", []))
    if sys.argv[1] == "before_start":
        before_start(roles, dependencies)
    elif sys.argv[1] == "after_start":
        after_start(roles, dependencies)
    else:
        exit(1) 


def before_start(roles, dependencies):
    print "Initializing " + socket.getfqdn() + " as '" + ", ".join(roles) + "'..."

    for role in roles:
        module = modules.get(role.upper())

        substitution = module.substitution() if hasattr(module, "substitution") else {}
        role_etc = os.path.join("/opt", "splunk-deployment", role)
        if os.path.isdir(role_etc):
            init_helpers.copy_etc_tree(
                role_etc,
                os.path.join(os.environ['SPLUNK_HOME']),
                substitution
            )

        if hasattr(module, "before_start"):
            module.before_start()

    if splunk.util.normalizeBoolean(os.environ.get("INIT_FORWARD_INDEX", False)):
        init_helpers.copy_etc_tree(
            os.path.join("/opt", "splunk-deployment", "_enable_forward_index"),
            os.path.join(os.environ['SPLUNK_HOME']),
            {
                "@INDEX_DISCOVERY_MASTER_URI@": os.environ.get("INIT_INDEX_DISCOVERY_MASTER_URI", "https://cluster-master:8089"),
                "@INDEX_DISCOVERY_PASS_4_SYMM_KEY@": os.environ.get("INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY", "indexdiscovery-changeme")
            }
        )

    for dependency in dependencies:
        url, role = dependency
        init_helpers.wait_dependency(url, role)

    # Allow to set any configurations with this
    for env, val in os.environ.iteritems():
        if env.startswith("INIT_CONF__"):
            parts = env.split("__")
            conf_file = None
            if len(parts) == 4:
                conf_file = os.path.join(os.environ["SPLUNK_HOME"], "etc", "system", "local", parts[1] + ".conf")
                parts = parts[2:]
            else:
                conf_file = os.path.join(os.environ["SPLUNK_HOME"], "etc", "apps", parts[1], "local", parts[2] + ".conf")
                parts = parts[3:]
            conf = splunk.clilib.cli_common.readConfFile(conf_file) if os.path.exists(conf_file) else {}
            conf.setdefault(parts[0], {})[parts[1]] = val
            init_helpers.write_conf_file(conf_file, conf)


def after_start(roles, dependencies):
    init_consul.wait_consul()
    init_consul.register_splunkd_service(roles)

    for role in roles:
        module = modules.get(role.upper())
        if hasattr(module, "after_start"):
            module.after_start()

    print "Initialized " + socket.getfqdn() + " as '" + ", ".join(roles) + "'."


if __name__ == "__main__":
    main()