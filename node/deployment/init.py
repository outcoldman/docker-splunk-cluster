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

import splunk.util


modules = {
    "CLUSTER_SLAVE": init_cluster_slave,
    "CLUSTER_MASTER": init_cluster_master,
    "CLUSTER_SEARCHHEAD": init_cluster_searchhead,
    "SHC_MEMBER": init_shc_member,
    "LICENSE_MASTER": init_license_master,
    "LICENSE_SLAVE": init_license_slave,
    "SHC_DEPLOYER": init_shc_deployer,
    "SHC_DEPLOYER_CLIENT": init_shc_deployer_client
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
        dependencies = []

        for role in roles:
            module = modules.get(role.upper())

            substitution = module.substitution() if hasattr(module, "substitution") else {}
            init_helpers.copy_etc_tree(
                os.path.join("/opt", "splunk-deployment", role, "etc"),
                os.path.join(os.environ['SPLUNK_HOME'], "etc"),
                substitution
            )

            configurations = module.configurations() if hasattr(module, "configurations") else {}
            kvstore |= configurations.get("components", {}).get("kvstore", False)
            web |= configurations.get("components", {}).get("web", False)
            indexing |= configurations.get("components", {}).get("indexing", False)
            dependencies.extend(configurations.get("dependencies", []))

            if hasattr(module, "before_start"):
                module.before_start()

        if "INIT_KVSTORE_ENABLED" in os.environ:
            kvstore = splunk.util.normalizeBoolean(os.environ.get("INIT_KVSTORE_ENABLED"))

        if "INIT_WEB_ENABLED" in os.environ:
            web = splunk.util.normalizeBoolean(os.environ.get("INIT_WEB_ENABLED"))

        if "INIT_INDEXING_ENABLED" in os.environ:
            indexing = splunk.util.normalizeBoolean(os.environ.get("INIT_INDEXING_ENABLED"))

        if not kvstore:
            init_helpers.copy_etc_tree(
                os.path.join("/opt", "splunk-deployment", "_disable_kvstore", "etc"),
                os.path.join(os.environ['SPLUNK_HOME'], "etc")
            )
            init_helpers.splunk_clean_kvstore()

        if not web:
            init_helpers.copy_etc_tree(
                os.path.join("/opt", "splunk-deployment", "_disable_web", "etc"),
                os.path.join(os.environ['SPLUNK_HOME'], "etc")
            )

        if not indexing:
            init_helpers.copy_etc_tree(
                os.path.join("/opt", "splunk-deployment", "_disable_indexing", "etc"),
                os.path.join(os.environ['SPLUNK_HOME'], "etc"),
                {
                    "@INDEX_DISCOVERY_MASTER_URI@": os.environ.get("INIT_INDEX_DISCOVERY_MASTER_URI", "https://cluster-master:8089"),
                    "@INDEX_DISCOVERY_PASS_4_SYMM_KEY@": os.environ.get("INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY", "indexdiscovery-changeme")
                }
            )
            init_helpers.splunk_clean_index()

        for dependency in dependencies:
            url, role = dependency
            init_helpers.wait_dependency(url, role)

        init_helpers.splunk_start()

        init_consul.wait_consul()
        init_consul.register_service(roles)

        for role in roles:
            module = modules.get(role.upper())
            if hasattr(module, "after_start"):
                module.after_start()

        print "Initialized " + os.environ['HOSTNAME'] + " as '" + ", ".join(roles) + "'."

if __name__ == "__main__":
    main()