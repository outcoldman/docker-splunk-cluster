#!/bin/bash

mkdir -p $SPLUNK_HOME/var/consul

/bin/consul \
    agent \
    -data-dir="$SPLUNK_HOME/var/consul" \
    -join="${CONSUL_HOST:-consul}" \
    -dc="${CONSUL_DC:-dc}" \
    -domain="${CONSUL_DOMAIN:-splunk}" \
