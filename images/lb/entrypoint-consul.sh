#!/bin/bash

mkdir -p /var/consul/data

/bin/consul \
    agent \
    -data-dir="/var/consul/data" \
    -retry-join="${CONSUL_HOST:-consul}" \
    -dc="${CONSUL_DC:-dc}" \
    -domain="${CONSUL_DOMAIN:-splunk}" \
    -advertise=$(ip addr list ${CONSUL_ADVERTISE_INTERFACE:-eth0} |grep "inet " |cut -d' ' -f6|cut -d/ -f1) \
    -http-port=8499 \
    -config-file="/etc/consul/consul.json"