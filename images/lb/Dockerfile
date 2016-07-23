FROM haproxy:1.6.6

MAINTAINER Denis Gladkikh <docker-splunk-cluster@denis.gladkikh.email>

# TODO:
# Important - this is an RC1 version, which will not exist on Hashicorp servers soon
# Upgrade to 0.16.0 when it will be ready https://releases.hashicorp.com/consul-template/
ENV CONSUL_TEMPLATE_VERSION=0.16.0-rc1
ENV CONSUL_TEMPLATE_SHA256SUMS=6e14968b400a3b8c82f7f6859100baa1c55603ce7533bc03fd2c929e2348bfe4

RUN apt-get update \
    && apt-get install -y wget unzip \
    && wget -qO /tmp/consul-template.zip https://releases.hashicorp.com/consul-template/${CONSUL_TEMPLATE_VERSION}/consul-template_${CONSUL_TEMPLATE_VERSION}_linux_amd64.zip \
    && echo "${CONSUL_TEMPLATE_SHA256SUMS}  /tmp/consul-template.zip" > /tmp/consul-template.sha256 \
    && sha256sum -c /tmp/consul-template.sha256 \
    && cd /bin \
    && unzip /tmp/consul-template.zip \
    && chmod +x /bin/consul-template \
    && rm /tmp/consul-template.zip \
    && rm /tmp/consul-template.sha256 \
    && apt-get purge -y --auto-remove wget unzip \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /bin/entrypoint-consul-template.sh
COPY template.ctmpl /usr/local/etc/consul/template.ctmpl
RUN chmod +x /bin/entrypoint-consul-template.sh

ENTRYPOINT /bin/entrypoint-consul-template.sh
