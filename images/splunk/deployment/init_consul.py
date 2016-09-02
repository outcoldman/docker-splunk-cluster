import os
import json
import time
import copy

import requests


def consul_get(path, **kwargs):
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


def consul_put(path, **kwargs):
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


def wait_consul():
    """
    We start consul using scripting input, which might require us to wait when it will be up.
    """
    for x in xrange(1, 300):
        response = consul_get("/status/leader")
        if response.text:
            return
        else:
            print "Waiting for consul leader. Leader = %s." % response.text
        time.sleep(1)
    print "FAILED. Consul did not have a leader."
    exit(1)


def register_splunkd_service(tags):
    register_service({
        "Name": "splunkd",
        "Tags": tags,
        "Port": 8089,
    }, checks=[{
        "TCP": "127.0.0.1:8089",
        "Interval": "60s"
    }, {
        "Script": "/opt/splunk/bin/splunk status",
        "Interval": "60s"
    }])


def register_service(service, checks=None):
    """
    Register local Service
    """
    response = consul_put("/agent/service/register", data=json.dumps(service))
    print "Registered Service: " + service["Name"]
    if checks:
        for index, check in enumerate(checks):
            check = copy.copy(check)
            check["Service"] = service["Name"]
            check["Name"] = "Check for %s - %d" % (service["Name"], index + 1) 
            response = consul_put("/agent/check/register", data=json.dumps(check))
            print "Registered additional check: %s." % check["Name"]
