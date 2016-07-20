import os

import init_helpers
import init_cluster_slave
import init_cluster_master
import init_shc_member


modules = {
    "CLUSTER_SLAVE": init_cluster_slave,
    "CLUSTER_MASTER": init_cluster_master,
    "SHC_MEMBER": init_shc_member
}


def main():
    """
    Initialize node
    """
    roles = [role.upper() for role in os.environ.get("SPLUNK_ROLES", "").split(",")]
    if roles:
        print "Initializing " + os.environ['HOSTNAME'] + " as '" + ", ".join(roles) + "'..."

        for role in roles:
            module = modules.get(role.upper())
            if module is None:
                print "Unknown role " + role
                exit(1)
            if hasattr(module, "before_stop"):
                module.before_stop()

        init_helpers.splunk_stop()

        for role in roles:
            module = modules.get(role.upper())

            substitution = module.substitution() if hasattr(module, "substitution") else {}
            init_helpers.copy_etc_tree(
                os.path.join("/opt", "splunk-deployment", role, "etc"),
                os.path.join(os.environ['SPLUNK_HOME'], "etc"),
                substitution
            )

            if hasattr(module, "before_start"):
                module.before_start()

        init_helpers.splunk_start()

        print "Initialized " + os.environ['HOSTNAME'] + " as '" + ", ".join(roles) + "'."

if __name__ == "__main__":
    main()