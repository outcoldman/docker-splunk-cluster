import os
import json
import time

import requests


def wait_consul():
    """
    We start consul using scripting input, which might require us to wait when it will be up.
    """
    for x in xrange(1, 300):
        try:
            response = requests.get("http://127.0.0.1:8500/v1/status/leader")
            if response.status_code == 200 and response.text:
                print "Consul is ready. Response = %d, Leader = %s." % (response.status_code, response.text)
                return
            print "Waiting for local consul. Response = %d, Leader = %s." % (response.status_code, response.text)
        except requests.exceptions.RequestException:
            print "Waiting for local consul."
        time.sleep(1)
    print "Failed to connect to local consul."
    exit(1)


def register_splunkd_service(tags):
    register_service({
        "Name": "splunkd",
        "Tags": tags,
        "Port": 8089,
        "Check": {
            "Script": "/opt/splunk/bin/splunk status",
            "Interval": "60s"
        }
    })


def register_splunkweb_service(tags):
    register_service({
        "Name": "splunkweb",
        "Tags": tags,
        "Port": 8000,
        "Check": {
            "HTTP": "http://127.0.0.1:8000/robots.txt",
            "Interval": "60s"
        }
    })


def register_kvstore_service(tags):
    register_service({
        "Name": "kvstore",
        "Tags": tags,
        "Port": 8191, 
        "Check": {
            "TCP": "127.0.0.1:8191",
            "Interval": "60s"
        }
    })


def register_service(service):
    """
    Register local Service
    """
    for x in xrange(1, 300):
        try:
            response = requests.put("http://127.0.0.1:8500/v1/agent/service/register", data=json.dumps(service))
            if response.status_code != 200:
                print "Failed to register service. %d. %s." % (response.status_code, response.text) 
                exit(1)
            print "Result of registering myself as a consul service. %d. %s." % (response.status_code, response.text)
            return
        except requests.exceptions.RequestException:
            print "Waiting for local consul."
        time.sleep(1)
    print "Failed to connect to local consul."
    exit(1)