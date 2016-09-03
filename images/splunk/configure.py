import os
import sys
import json
import urllib
import time
import base64
import socket
import re
import glob
import subprocess

import requests

import splunk.clilib.cli_common
import splunk.util


var_expandvars_re = re.compile(r'\AENV\((.*)\)$')
var_shell_re = re.compile(r'\ASHELL\((.*)\)$')


def main():
    """
    Initialize node. Can run before splunk started and after splunk started
    """
    if sys.argv[1] == "before_start":
        before_start()
    elif sys.argv[1] == "after_start":
        after_start()
    else:
        exit(1) 


def before_start():
    """
    Before start:
    - add licenses from /opt/splunk-licenses
    - using INIT_WAIT_SPLUNK can wait for another Splunk instances, where
        INIT_WAIT_SPLUNK can be defined as "https://another-splunk-instance:8089,cluster-master",
        where second value is the server role which needs to be check.
    - using CONF__ notation you can define any configuration, examples
        CONF__[{location_under_splunk_home}__]{conf_file}__{stanza}__{key}=value
        If location_under_splunk_home is not specified - system is used.
    """
    __add_licenses()

    # Allow to set any configurations with this
    conf_updates = {}
    for env, val in os.environ.iteritems():
        if env.startswith("INIT_WAIT_SPLUNK"):
            parts = val.split(",")
            url = parts[0]
            __wait_dependency(url)
            for i in xrange(1, len(parts)):
                __wait_dependency(url, parts[i])
        elif env.startswith("CONF__"):
            parts = env.split("__")[1:]
            conf_file_name = None
            parent = None
            conf_folder = "system"
            if len(parts) == 4:
                conf_folder = parts[0]
                parts = parts[1:]
            conf_folder_full = __get_conf_folder_full(conf_folder, parent)
            conf_file = os.path.join(conf_folder_full, "local", parts[0] + ".conf")
            conf_updates.setdefault(conf_file, {}).setdefault(parts[1], {})[parts[2]] = __get_value(val)

    for conf_file, conf_update in conf_updates.iteritems():
        conf = splunk.clilib.cli_common.readConfFile(conf_file) if os.path.exists(conf_file) else {}
        for stanza, values in conf_update.iteritems():
            dest_stanza = conf.setdefault(stanza, {})
            dest_stanza.update(values)
        if "default" in conf and not conf["default"]:
            del conf["default"]
        folder = os.path.dirname(conf_file)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        splunk.clilib.cli_common.writeConfFile(conf_file, conf)


def after_start():
    """
    After start wait for consul, register requires services, where services defined as
    INIT_CONSUL_SERVICE[anything]=service_name,port[,check_type,check,interval].
    INIT_SHCLUSTER_AUTOBOOTSTRAP can be used for SHC member to autobootstrap SHC.
    """
    __wait_consul()
    for env, val in os.environ.iteritems():
        if env.startswith("INIT_CONSUL_SERVICE"):
            vals = val.split(",")
            service = {
                "Name": vals[0],
                "Port": int(vals[1])
            }
            checks = None
            if len(vals) > 2:
                checks = [{vals[2]: vals[3], "Interval": vals[4]}]
            print service
            print checks
            __register_service(service, checks)

    if "INIT_SHCLUSTER_AUTOBOOTSTRAP" in os.environ:
        __shc_membership()


def __get_value(val):
    var_expand_match = var_expandvars_re.match(val)
    if var_expand_match:
        return os.path.expandvars(var_expand_match.groups()[0])
    var_shell_match = var_shell_re.match(val)
    if var_shell_match:
        return subprocess.check_output(var_expand_match.groups()[0], shell=True)
    return val


def __get_conf_folder_full(conf_folder, parent):
    if conf_folder == "system":
        return os.path.join(os.environ["SPLUNK_HOME"], "etc", conf_folder)
    else:
        return os.path.join(os.environ["SPLUNK_HOME"], conf_folder)


def __add_licenses():
    while True:
        if os.path.isdir(os.path.join("/opt", "splunk-licenses")):
            licenses = glob.glob(os.path.join("/opt", "splunk-licenses", "*.lic"))
            if licenses:
                # Adding all licenses one by one and break
                for license in licenses:
                    args = [
                        "add",
                        "licenses",
                        "-auth", "admin:changeme",
                        license
                    ]
                    __splunk_execute(args)
                break

        if splunk.util.normalizeBoolean(os.environ.get("INIT_WAIT_LICENSE", "False")):
            print "Waiting for license files under /opt/splunk-deployment/licenses/"
            time.sleep(1)
        else:
            break


def __shc_membership():
    """
    Using consul we will auto bootstrap the SHC or add node to the existing cluster
    """
    # Create Session in Consul
    response = __consul_put(
        "/session/create",
        data=json.dumps({"Name": "SHC-Member", "LockDelay": "15s", "TTL": "600s"}))
    session_id = response.json()["ID"]

    __verify_shc_membership(session_id)

    __consul_put("/session/destroy/" + urllib.quote(session_id))


def __verify_shc_membership(consul_session_id):
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
    key_member = urllib.quote(os.environ.get("INIT_SHCLUSTERING_SHCLUSTER_LABEL", "shcluster")) + "/members/" + urllib.quote(os.environ.get("INIT_SHCLUSTERING_HOSTNAME", socket.getfqdn()))

    for x in xrange(1, 1800):
        response = __consul_put("/kv/" + key_bootstrap, params={"acquire": consul_session_id})
        print "Result of acquiring the bootstrap lock. %d. %s." % (response.status_code, response.text)
        locked = splunk.util.normalizeBoolean(response.text)
        if locked:
            response = __consul_put("/kv/" + key_member, data=("https://%s:8089" % os.environ.get("INIT_SHCLUSTERING_HOSTNAME", socket.getfqdn())))
            print "Result of saving myself to members list. %d. %s." % (response.status_code, response.text)
            response = __consul_get("/kv/" + key_members, params={"recurse": True})
            print "Result of getting members list. %d. %s." % (response.status_code, response.text)
            records = response.json()
            if len(records) == autobootstrap:
                members = ",".join(base64.b64decode(record["Value"]) for record in records)
                print "Bootstrapping with '%s'." % members
                __splunk_execute([
                    "bootstrap",
                    "shcluster-captain",
                    "-auth", "admin:changeme",
                    "-servers_list", members
                ])
            elif len(records) > autobootstrap:
                # adding to existing SHC
                print "Adding to existing SHC."
                __splunk_execute([
                    "add",
                    "shcluster-member",
                    "-auth", "admin:changeme",
                    "-current_member_uri", next(base64.b64decode(record["Value"]) for record in records)
                ])

            response = __consul_put("/kv/" + key_bootstrap, params={"release": consul_session_id})
            print "Result of released the leader lock. %d. %s." % (response.status_code, response.text)
            # We are done
            return
        time.sleep(1)


def __splunk_execute(args):
    """
    Execute splunk with arguments
    """
    sys.stdout.flush()
    sys.stderr.flush()
    splunk_args = [os.path.join(os.environ['SPLUNK_HOME'], "bin", "splunk")]
    splunk_args.extend(args)
    subprocess.check_call(splunk_args)
    sys.stdout.flush()
    sys.stderr.flush()


def __wait_dependency(uri, server_role=None):
    """
    Wait 5 minutes for dependency
    """
    for x in xrange(1, 300):
        try:
            # This url does not require authentication, ignore certificate
            response = requests.get(uri + "/services/server/info?output_mode=json", verify=False)
            if response.status_code == 200:
                server_roles = response.json()["entry"][0]["content"]["server_roles"]
                if not server_role or server_role in server_roles:
                    return
                else:
                    print "Waiting for " + server_role + " in " + uri + " got " + ", ".join(server_roles) + "."
            else:
                print "Waiting for "+ server_role + " in " + uri + "."
        except requests.exceptions.RequestException as exception:
            print "Waiting for " + server_role + " in " + uri + ". Exception: " + str(exception)
        time.sleep(1)
    print "Failed to connect to " + uri + " and check server role " + server_role
    exit(1)


def __consul_get(path, **kwargs):
    for x in xrange(1, 300):
        try:
            response = requests.get("http://127.0.0.1:8500/v1" + path, **kwargs)
            if response.status_code == 200:
                return response
            print "Failed to make GET request to consul. Response = %d, Leader = %s." % (response.status_code, response.text)
        except requests.exceptions.RequestException as ex:
            print "Failed to make GET request to consul. " + str(ex)
        time.sleep(1)
    print "FAILED. Could not make GET request to consul."
    exit(1)


def __consul_put(path, **kwargs):
    for x in xrange(1, 300):
        try:
            response = requests.put("http://127.0.0.1:8500/v1" + path, **kwargs)
            if response.status_code == 200:
                return response
            print "Failed to make PUT request to consul. Response = %d, Leader = %s." % (response.status_code, response.text)
        except requests.exceptions.RequestException as ex:
            print "Failed to make PUT request to consul. " + str(ex)
        time.sleep(1)
    print "FAILED. Could not make PUT request to consul."
    exit(1)


def __wait_consul():
    """
    We start consul using scripting input, which might require us to wait when it will be up.
    """
    for x in xrange(1, 300):
        response = __consul_get("/status/leader")
        if response.text:
            return
        else:
            print "Waiting for consul leader. Leader = %s." % response.text
        time.sleep(1)
    print "FAILED. Consul did not have a leader."
    exit(1)


def __register_service(service, checks=None):
    """
    Register local Service
    """
    response = __consul_put("/agent/service/register", data=json.dumps(service))
    print "Registered Service: " + service["Name"]
    if checks:
        for index, check in enumerate(checks):
            check = copy.copy(check)
            check["Service"] = service["Name"]
            check["Name"] = "Check for %s - %d" % (service["Name"], index + 1) 
            response = __consul_put("/agent/check/register", data=json.dumps(check))
            print "Registered additional check: %s." % check["Name"]


if __name__ == "__main__":
    main()