import os
import json
import time

import requests


def wait_consul():
    for x in xrange(1, 300):
        try:
            response = requests.get("http://127.0.0.1:8500/v1/status/leader")
            if response.status_code == 200 and response.text:
                return
            print "Waiting for local consul. Response = %d, Leader = %s." % (response.status_code, response.text)
        except requests.exceptions.RequestException:
            print "Waiting for local consul."
            pass
        time.sleep(1)
    print "Failed to connect to local consul."
    exit(1)


def register_service(roles):
    response = requests.put("http://127.0.0.1:8500/v1/agent/service/register", data=json.dumps({
        "Name": os.environ['HOSTNAME'],
        "Tags": roles,
        "Port": 8089,
        "Check": {
            "Script": "/opt/splunk/bin/splunk status",
            "Interval": "10s"
        }
    }))
    if response.status_code != 200:
        print "Failed to register service. %d. %s." % (response.status_code, response.text) 
        exit(1)