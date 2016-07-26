#!/bin/bash

/bin/consul-template \
    -consul 127.0.0.1:8499 \
    -template "/usr/local/etc/consul/template.ctmpl:/usr/local/etc/haproxy/haproxy.cfg" \
    -exec "haproxy -f /usr/local/etc/haproxy/haproxy.cfg"
