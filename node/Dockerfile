FROM outcoldman/splunk:6.4.2

MAINTAINER Denis Gladkikh <docker-splunk-cluster@denis.gladkikh.email>

COPY ./ /opt/splunk-deployment/

ENV SPLUNK_CMD "cmd python /opt/splunk-deployment/init.py"