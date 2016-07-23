#!/bin/sh

/usr/local/bin/docker-entrypoint.sh \
    agent \
    -bootstrap-expect=${CONSUL_BOOTSTRAP_EXPECT:-"1"} \
    -data-dir=${CONSUL_DATA_DIR:-"/consul/data"} \
    -dc=${CONSUL_DC:-"dc"} \
    -domain=${CONSUL_DOMAIN:-"splunk"} \
    -server \
    -ui \
    -client=${CONSUL_CLIENT:-"0.0.0.0"} \
    -advertise=$(ip addr list ${CONSUL_ADVERTISE_INTERFACE:-eth0} |grep "inet " |cut -d' ' -f6|cut -d/ -f1) \
    -retry-join=${CONSUL_JOIN:-"consul"}