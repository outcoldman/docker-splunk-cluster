#!/bin/sh

/bin/consul-template \
    -consul ${CONSUL_HOST:-"consul:8500"} \
    -template "/usr/local/etc/consul/template.ctmpl:/usr/local/etc/haproxy/haproxy.cfg" \
    -exec "/docker-entrypoint.sh haproxy -f /usr/local/etc/haproxy/haproxy.cfg"
