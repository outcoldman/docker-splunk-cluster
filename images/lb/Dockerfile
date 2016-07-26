FROM debian:jessie

MAINTAINER Denis Gladkikh <docker-splunk-cluster@denis.gladkikh.email>

# See checksums https://releases.hashicorp.com/consul/0.6.4/consul_0.6.4_SHA256SUMS
ENV CONSUL_VERSION=0.6.4
ENV CONSUL_SHA256SUMS=abdf0e1856292468e2c9971420d73b805e93888e006c76324ae39416edcf0627

# TODO:
# Important - this is an RC1 version, which will not exist on Hashicorp servers soon
# Upgrade to 0.16.0 when it will be ready https://releases.hashicorp.com/consul-template/
ENV CONSUL_TEMPLATE_VERSION=0.16.0-rc1
ENV CONSUL_TEMPLATE_SHA256SUMS=6e14968b400a3b8c82f7f6859100baa1c55603ce7533bc03fd2c929e2348bfe4

ENV SUPERVISOR_LOGGING_MD5SUMS=05dc40e5b966f6ad8f038f3524e1701d

# Install consul, consul-template, haproxy, supervisor, supervisor-logging
RUN apt-get update \
    && apt-get install -y wget unzip supervisor haproxy python-setuptools \
    && wget -qO /tmp/consul.zip https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_linux_amd64.zip \
    && echo "${CONSUL_SHA256SUMS}  /tmp/consul.zip" > /tmp/consul.sha256 \
    && sha256sum -c /tmp/consul.sha256 \
    && cd /bin \
    && unzip /tmp/consul.zip \
    && chmod +x /bin/consul \
    && rm /tmp/consul.zip \
    && rm /tmp/consul.sha256 \
    && wget -qO /tmp/consul-template.zip https://releases.hashicorp.com/consul-template/${CONSUL_TEMPLATE_VERSION}/consul-template_${CONSUL_TEMPLATE_VERSION}_linux_amd64.zip \
    && echo "${CONSUL_TEMPLATE_SHA256SUMS}  /tmp/consul-template.zip" > /tmp/consul-template.sha256 \
    && sha256sum -c /tmp/consul-template.sha256 \
    && cd /bin \
    && unzip /tmp/consul-template.zip \
    && chmod +x /bin/consul-template \
    && rm /tmp/consul-template.zip \
    && rm /tmp/consul-template.sha256 \
    && cd /tmp \
    && wget -qO /tmp/supervisor-logging.tar.gz https://pypi.python.org/packages/f0/9e/2171863fc1942be526d626af34d0d7e022cb5b1b7799ac1a25d78af99815/supervisor-logging-0.0.9.tar.gz#md5=05dc40e5b966f6ad8f038f3524e1701d \
    && echo "${SUPERVISOR_LOGGING_MD5SUMS}  /tmp/supervisor-logging.tar.gz" > /tmp/supervisor-logging.md5 \
    && md5sum -c /tmp/supervisor-logging.md5 \
    && tar -xvf supervisor-logging.tar.gz \
    && cd supervisor-logging-0.0.9 \
    && python setup.py install \
    && cd /bin \
    && rm -fR /tmp/supervisor-logging-0.0.9 /tmp/supervisor-logging.tar.gz \
    && apt-get purge -y --auto-remove wget unzip python-setuptools \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint-*.sh /sbin/
COPY template.ctmpl /usr/local/etc/consul/template.ctmpl
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY consul.json /etc/consul/consul.json
RUN chmod +x /sbin/entrypoint-*.sh

VOLUME ["/var/consul"]

ENV SYSLOG_SERVER syslog
ENV SYSLOG_PORT 1514
ENV SYSLOG_PROTO udp

CMD ["/usr/bin/supervisord"]