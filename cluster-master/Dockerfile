FROM outcoldman/splunk:6.4.2

MAINTAINER Denis Gladkikh <docker-splunk@denis.gladkikh.email>

ADD init.py /opt/splunk-deployment/
ADD etc /opt/splunk-deployment/etc

ADD *.lic /opt/splunk-deployment/

ENV SPLUNK_CMD "cmd python /opt/splunk-deployment/init.py"