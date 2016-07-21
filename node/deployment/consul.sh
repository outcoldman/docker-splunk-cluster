#!/bin/bash

mkdir -p $SPLUNK_HOME/var/consul/data

/bin/consul \
    agent \
    -data-dir="$SPLUNK_HOME/var/consul/data" \
    -join="${CONSUL_HOST:-consul}" \
    -dc="${CONSUL_DC:-dc}" \
    -domain="${CONSUL_DOMAIN:-splunk}" \
    -encrypt="$CONSUL_ENCRYPT"