import os
import json
import urllib
import time
import base64
import socket

import splunk.util

import init_helpers
import init_consul


def configurations():
    return {
        "components": {
            "kvstore": True,
            "web": True,
            "indexing": False,
            "dmc": False
        }
    }


def substitution():
    return {
        "@SHCLUSTERING_PASS_4_SYMM_KEY@": os.environ.get("INIT_SHCLUSTERING_PASS_4_SYMM_KEY", "shclustering-changeme"),
        "@SHCLUSTERING_MGMT_URI@": os.environ.get("INIT_SHCLUSTERING_MGMT_URI", "https://%s:8089" % socket.getfqdn()),
        "@SHCLUSTERING_REPLICATION_FACTOR@": os.environ.get("INIT_SHCLUSTERING_REPLICATION_FACTOR", "3"),
        "@SHCLUSTERING_SHCLUSTER_LABEL@": os.environ.get("INIT_SHCLUSTERING_SHCLUSTER_LABEL", "shcluster")
    }


def after_start():
    """
    Using consul we will auto bootstrap the SHC or add node to the existing cluster
    """
    # Create Session in Consul
    response = init_consul.consul_put(
        "/session/create",
        data=json.dumps({"Name": "SHC-Member", "LockDelay": "15s", "TTL": "600s"}))
    session_id = response.json()["ID"]

    verify_membership(session_id)

    init_consul.consul_put("/session/destroy/" + urllib.quote(session_id))


def verify_membership(consul_session_id):
    """
    Verify that current SHC Member is in SHC. If not - add it.
    1. Create consul session.
    2. Try to be a leader.
    3. Put yourself in list of members.
    4. Get list of all SHC registered members.
    5. If see that number = INIT_SHCLUSTER_AUTOBOOTSTRAP - do bootstrap.
    6. If number is more than INIT_SHCLUSTER_AUTOBOOTSTRAP - add yourself to SHC.
    7. Release leadership.
    8. Destroy session.
    """
    autobootstrap = int(os.environ.get("INIT_SHCLUSTER_AUTOBOOTSTRAP", "3"))
    key_bootstrap = urllib.quote(os.environ.get("INIT_SHCLUSTERING_SHCLUSTER_LABEL", "shcluster")) + "/lock/bootstrap"
    key_members = urllib.quote(os.environ.get("INIT_SHCLUSTERING_SHCLUSTER_LABEL", "shcluster")) + "/members"
    key_member = urllib.quote(os.environ.get("INIT_SHCLUSTERING_SHCLUSTER_LABEL", "shcluster")) + "/members/" + urllib.quote(socket.getfqdn())

    for x in xrange(1, 1800):
        response = init_consul.consul_put("/kv/" + key_bootstrap, params={"acquire": consul_session_id})
        print "Result of acquiring the bootstrap lock. %d. %s." % (response.status_code, response.text)
        locked = splunk.util.normalizeBoolean(response.text)
        if locked:
            response = init_consul.consul_put("/kv/" + key_member, data=("https://%s:8089" % socket.getfqdn()))
            print "Result of saving myself to members list. %d. %s." % (response.status_code, response.text)
            response = init_consul.consul_get("/kv/" + key_members, params={"recurse": True})
            print "Result of getting members list. %d. %s." % (response.status_code, response.text)
            records = response.json()
            if len(records) == autobootstrap:
                members = ",".join(base64.b64decode(record["Value"]) for record in records)
                print "Bootstrapping with '%s'." % members
                init_helpers.splunk_execute([
                    "bootstrap",
                    "shcluster-captain",
                    "-auth", "admin:changeme",
                    "-servers_list", members
                ])
            elif len(records) > autobootstrap:
                # adding to existing SHC
                print "Adding to existing SHC."
                init_helpers.splunk_execute([
                    "add",
                    "shcluster-member",
                    "-auth", "admin:changeme",
                    "-current_member_uri", next(base64.b64decode(record["Value"]) for record in records)
                ])

            response = init_consul.consul_put("/kv/" + key_bootstrap, params={"release": consul_session_id})
            print "Result of released the leader lock. %d. %s." % (response.status_code, response.text)
            # We are done
            return
        time.sleep(1)