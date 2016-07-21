FROM outcoldman/splunk:6.4.2

MAINTAINER Denis Gladkikh <docker-splunk-cluster@denis.gladkikh.email>

# See checksums https://releases.hashicorp.com/consul/0.6.4/consul_0.6.4_SHA256SUMS
ENV CONSUL_VERSION=0.6.4
ENV CONSUL_SHA256SUMS=abdf0e1856292468e2c9971420d73b805e93888e006c76324ae39416edcf0627

RUN apt-get update \
    && apt-get install -y wget unzip \
    && wget -qO /tmp/consul.zip https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_linux_amd64.zip \
    && echo "${CONSUL_SHA256SUMS}  /tmp/consul.zip" > /tmp/consul.sha256 \
    && sha256sum -c /tmp/consul.sha256 \
    && cd /bin \
    && unzip /tmp/consul.zip \
    && chmod +x /bin/consul \
    && rm /tmp/consul.zip \
    && rm /tmp/consul.sha256 \
    && apt-get purge -y --auto-remove wget unzip \
    && rm -rf /var/lib/apt/lists/*

COPY deployment /opt/splunk-deployment/
COPY consul_indexes.conf ${SPLUNK_BACKUP_DEFAULT_ETC}/etc/system/local/indexes.conf
COPY consul_inputs.conf ${SPLUNK_BACKUP_DEFAULT_ETC}/etc/system/local/inputs.conf
COPY consul.sh ${SPLUNK_HOME}/bin/scripts/consul.sh

RUN chmod +x ${SPLUNK_HOME}/bin/scripts/consul.sh

ENV SPLUNK_CMD "cmd python /opt/splunk-deployment/init.py"
