FROM alpine:3.3

MAINTAINER Denis Gladkikh <docker-splunk-cluster@denis.gladkikh.email>

ENV CONSUL_TEMPLATE_VERSION=0.15.0
ENV CONSUL_TEMPLATE_SHA256SUMS=b7561158d2074c3c68ff62ae6fc1eafe8db250894043382fb31f0c78150c513a

RUN apk add --no-cache ca-certificates \ 
    && cd /tmp/ \
    && wget -qO /tmp/consul-template.zip https://releases.hashicorp.com/consul-template/${CONSUL_TEMPLATE_VERSION}/consul-template_${CONSUL_TEMPLATE_VERSION}_linux_amd64.zip \
    && echo "${CONSUL_TEMPLATE_SHA256SUMS}  /tmp/consul-template.zip" > /tmp/consul-template.sha256 \
    && sha256sum -c /tmp/consul-template.sha256 \
    && cd /bin \
    && unzip /tmp/consul-template.zip \
    && chmod +x /bin/consul-template \
    && rm /tmp/consul-template.zip \
    && rm /tmp/consul-template.sha256

COPY entrypoint.sh /bin/entrypoint.sh
COPY template.ctmpl /usr/local/etc/consul/template.ctmpl
RUN chmod +x /bin/entrypoint.sh

ENTRYPOINT /bin/entrypoint.sh
