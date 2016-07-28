#!/bin/sh

/bin/consul \
    agent \
    -bootstrap-expect=${CONSUL_BOOTSTRAP_EXPECT:-"1"} \
    -data-dir=${CONSUL_DATA_DIR:-"/consul/data"} \
    -dc=${CONSUL_DC:-"dc"} \
    -domain=${CONSUL_DOMAIN:-"splunk"} \
    -server \
    -ui \
    -client=${CONSUL_CLIENT:-"127.0.0.1"} \
    -advertise=$(ip addr list ${CONSUL_ADVERTISE_INTERFACE:-eth0} | grep "inet " | cut -d' ' -f6| cut -d/ -f1 | head -1) \
    -retry-join=${CONSUL_JOIN:-"consul"} \
    -config-file="/etc/consul/consul.json"
