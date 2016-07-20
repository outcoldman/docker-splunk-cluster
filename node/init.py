import os

def main():
    """
    Initialize node
    """
    roles = os.environ.get("SPLUNK_ROLES", "").split(",")
    if roles:

        for role in roles:
            print "Initializing role '" + role.upper() + "'..."
            if role.upper() == "CLUSTER_SLAVE":
                import init_cluster_slave
            elif role.upper() == "CLUSTER_MASTER":
                import init_cluster_master
            elif role.upper() == "SHC_MEMBER":
                import init_shc_member

if __name__ == "__main__":
    main()