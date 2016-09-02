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


components = [
    "dmc",
    "indexing",
    "kvstore",
    "web"
]


def main():
    """
    Initialize node
    """
    roles = [role.upper() for role in os.environ.get("SPLUNK_ROLES", "").split(",")]
    dependencies = []
    splunk_components = dict((component, False) for component in components)
    for role in roles:
        module = modules.get(role.upper())
        configurations = module.configurations() if hasattr(module, "configurations") else {}
        module_components = configurations.get("components", {})
        for component in components:
            splunk_components[component] |= module_components.get(component, False)
        dependencies.extend(configurations.get("dependencies", []))
    if sys.argv[1] == "before_start":
        before_start(roles, dependencies, splunk_components)
    elif sys.argv[1] == "after_start":
        after_start(roles, dependencies, splunk_components)
    else:
        exit(1) 


def before_start(roles, dependencies, splunk_components):
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

    for component in components:
        envvar = "INIT_%s_ENABLED" % component.upper()
        if envvar in os.environ:
            splunk_components[component] = splunk.util.normalizeBoolean(os.environ.get(envvar))

    if not splunk_components["kvstore"]:
        init_helpers.copy_etc_tree(
            os.path.join("/opt", "splunk-deployment", "_disable_kvstore"),
            os.path.join(os.environ['SPLUNK_HOME'])
        )
        init_helpers.splunk_clean_kvstore()

    if not splunk_components["web"]:
        init_helpers.copy_etc_tree(
            os.path.join("/opt", "splunk-deployment", "_disable_web"),
            os.path.join(os.environ['SPLUNK_HOME'])
        )
    else:
        prefix = os.environ.get("INIT_WEB_SETTINGS_PREFIX")
        if prefix:
            init_helpers.set_web_prefix(prefix)
        init_helpers.set_login_content("Roles:<br/><ul><li>" + "</li><li>".join(roles) + "</li></ul>")

    if not splunk_components["indexing"]:
        init_helpers.copy_etc_tree(
            os.path.join("/opt", "splunk-deployment", "_disable_indexing"),
            os.path.join(os.environ['SPLUNK_HOME']),
            {
                "@INDEX_DISCOVERY_MASTER_URI@": os.environ.get("INIT_INDEX_DISCOVERY_MASTER_URI", "https://cluster-master:8089"),
                "@INDEX_DISCOVERY_PASS_4_SYMM_KEY@": os.environ.get("INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY", "indexdiscovery-changeme")
            }
        )

    if not splunk_components["dmc"]:
        init_helpers.copy_etc_tree(
            os.path.join("/opt", "splunk-deployment", "_disable_dmc"),
            os.path.join(os.environ['SPLUNK_HOME'])
        )

    for dependency in dependencies:
        url, role = dependency
        init_helpers.wait_dependency(url, role)

    server_name = os.environ.get("INIT_SERVER_GENERAL_SERVERNAME", socket.getfqdn())
    if server_name:
        init_helpers.set_server_name(server_name)

    default_host = os.environ.get("INIT_INPUTS_DEFAULT_HOST", socket.getfqdn())
    if default_host:
        init_helpers.set_default_host(default_host)


def after_start(roles, dependencies, splunk_components):
    init_consul.wait_consul()
    init_consul.register_splunkd_service(roles)
    if splunk_components["web"]:
        init_consul.register_splunkweb_service(roles)
    if splunk_components["kvstore"]:
        init_consul.register_kvstore_service(roles)

    for role in roles:
        module = modules.get(role.upper())
        if hasattr(module, "after_start"):
            module.after_start()

    print "Initialized " + socket.getfqdn() + " as '" + ", ".join(roles) + "'."


if __name__ == "__main__":
    main()