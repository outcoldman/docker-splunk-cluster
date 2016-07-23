import os

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
import init_hw_forwarder
import init_dmc

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
    "HW_FORWARDER": init_hw_forwarder,
    "DMC": init_dmc
}


def main():
    """
    Initialize node
    """
    roles = [role.upper() for role in os.environ.get("SPLUNK_ROLES", "").split(",")]
    if roles:
        print "Initializing " + os.environ['HOSTNAME'] + " as '" + ", ".join(roles) + "'..."

        # Wait for local instance
        init_helpers.wait_local()
        init_consul.wait_consul()

        for role in roles:
            module = modules.get(role.upper())
            if module is None:
                print "Unknown role " + role
                exit(1)
            if hasattr(module, "before_stop"):
                module.before_stop()

        init_helpers.splunk_stop()

        kvstore = False
        web = False
        indexing = False
        dmc = False
        dependencies = []

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

            configurations = module.configurations() if hasattr(module, "configurations") else {}
            kvstore |= configurations.get("components", {}).get("kvstore", False)
            web |= configurations.get("components", {}).get("web", False)
            indexing |= configurations.get("components", {}).get("indexing", False)
            dmc |= configurations.get("components", {}).get("dmc", False)
            dependencies.extend(configurations.get("dependencies", []))

            if hasattr(module, "before_start"):
                module.before_start()

        if "INIT_KVSTORE_ENABLED" in os.environ:
            kvstore = splunk.util.normalizeBoolean(os.environ.get("INIT_KVSTORE_ENABLED"))

        if "INIT_WEB_ENABLED" in os.environ:
            web = splunk.util.normalizeBoolean(os.environ.get("INIT_WEB_ENABLED"))

        if "INIT_INDEXING_ENABLED" in os.environ:
            indexing = splunk.util.normalizeBoolean(os.environ.get("INIT_INDEXING_ENABLED"))

        if "INIT_DMC" in os.environ:
            indexing = splunk.util.normalizeBoolean(os.environ.get("INIT_DMC"))

        if not kvstore:
            init_helpers.copy_etc_tree(
                os.path.join("/opt", "splunk-deployment", "_disable_kvstore"),
                os.path.join(os.environ['SPLUNK_HOME'])
            )
            init_helpers.splunk_clean_kvstore()

        if not web:
            init_helpers.copy_etc_tree(
                os.path.join("/opt", "splunk-deployment", "_disable_web"),
                os.path.join(os.environ['SPLUNK_HOME'])
            )
        else:
            prefix = os.environ.get("INIT_WEB_SETTINGS_PREFIX")
            if prefix:
                init_helpers.set_web_prefix(prefix)
            init_helpers.set_login_content("Roles:<br/><ul><li>" + "</li><li>".join(roles) + "</li></ul>")

        if not indexing:
            init_helpers.copy_etc_tree(
                os.path.join("/opt", "splunk-deployment", "_disable_indexing"),
                os.path.join(os.environ['SPLUNK_HOME']),
                {
                    "@INDEX_DISCOVERY_MASTER_URI@": os.environ.get("INIT_INDEX_DISCOVERY_MASTER_URI", "https://cluster-master:8089"),
                    "@INDEX_DISCOVERY_PASS_4_SYMM_KEY@": os.environ.get("INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY", "indexdiscovery-changeme")
                }
            )

        if not dmc:
            init_helpers.copy_etc_tree(
                os.path.join("/opt", "splunk-deployment", "_disable_dmc"),
                os.path.join(os.environ['SPLUNK_HOME'])
            )

        for dependency in dependencies:
            url, role = dependency
            init_helpers.wait_dependency(url, role)

        init_helpers.splunk_start()

        init_consul.wait_consul()
        init_consul.register_splunkd_service(roles)
        if web:
            init_consul.register_splunkweb_service(roles)
        if kvstore:
            init_consul.register_kvstore_service(roles)

        for role in roles:
            module = modules.get(role.upper())
            if hasattr(module, "after_start"):
                module.after_start()

        print "Initialized " + os.environ['HOSTNAME'] + " as '" + ", ".join(roles) + "'."

if __name__ == "__main__":
    main()