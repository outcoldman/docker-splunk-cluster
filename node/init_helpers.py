import os
import errno
import shutil
import subprocess
import sys
import time

import splunk.clilib.cli_common

import requests


def mkdir_p(path):
    """
    mkdir -p implementation, ref http://stackoverflow.com/a/600612/421143
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def copy_etc_tree(src, dst, subs=None):
    """
    Smart copy files in etc folder.
    If see that destination file exists - overwrite confs.
    Otherwise just override files.
    """
    names = os.listdir(src)
    mkdir_p(dst)
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        if os.path.isdir(srcname):
            copy_etc_tree(srcname, dstname, subs)
        else:
            _, ext = os.path.splitext(name)
            if ext == ".conf":
                src_conf = splunk.clilib.cli_common.readConfFile(srcname)
                dst_conf = splunk.clilib.cli_common.readConfFile(dstname) if os.path.exists(dstname) else {}
                for stanza, values in src_conf.iteritems():
                    dest_stanza = dst_conf.setdefault(stanza, {})
                    for key, value in values.iteritems():
                        if subs:
                            for old, new in subs.iteritems():
                                value = value.replace(old, new)
                        dest_stanza[key] = value
                splunk.clilib.cli_common.writeConfFile(dstname, dst_conf)
            else:
                shutil.copyfile(srcname, dstname)


def splunk_stop():
    """
    Stop splunk
    """
    splunk_execute(["stop"])


def splunk_start():
    """
    Start splunk
    """
    splunk_execute(["start"])


def splunk_clean_all():
    """
    Clean local data
    """
    splunk_execute([
        "clean",
        "all",
        "-f"
    ])


def splunk_clean_kvstore():
    """
    Clean local kvstore
    """
    splunk_execute([
        "clean",
        "kvstore",
        "-local",
        "-f"
    ])


def splunk_clean_index():
    """
    Clean local indexes
    """
    splunk_execute([
        "clean",
        "eventdata",
        "-f"
    ])


def splunk_execute(args):
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


def wait_dependency(uri, server_role):
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
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    print "Failed to connect to " + uri + " and check server role " + server_role
    exit(1)


def wait_local():
    """
    Wait 5 minutes for local node.
    KVStore is usually last of the initialization process. When it is ready, whole node is functional
    """
    for x in xrange(1, 300):
        try:
            # This url does not require authentication, ignore certificate
            response = requests.get("https://localhost:8089/services/server/info?output_mode=json", verify=False)
            if response.status_code == 200:
                return
            else:
                print "Waiting for local node to be ready."
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    print "Failed to connect to local node."
    exit(1)