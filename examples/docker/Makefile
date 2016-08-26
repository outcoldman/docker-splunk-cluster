# With license master

SPLUNK_VERSION=6.4.3

clean-lm:
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml kill
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml rm -v -f

build-lm: build

deploy-lm:
	@echo "Verifying that at least one *.lic file exist"
	ls *.lic 1> /dev/null 2>&1;
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml up -d license-master
	ls *.lic | xargs -I @ docker cp @ $$(docker ps -qa --filter=label=splunk.cluster=license-master):/opt/splunk-deployment/licenses/
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml up -d
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml scale cluster-slave=4 shc-member=3 data-collector-hec=2
	@echo "Use 'docker-compose -f docker-compose.yml -f docker-compose.license-master.yml logs -f cluster-master' to wait for Initialized cluster-master as Cluster Master"

# Without license master

clean:
	docker-compose -f docker-compose.yml kill
	docker-compose -f docker-compose.yml rm -v -f

build:
	cd ./../../images/splunk && docker build -t outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION) -t outcoldman/docker-splunk-cluster:latest .
	cd ./../../images/lb && docker build -t outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION)-lb -t outcoldman/docker-splunk-cluster:latest-lb .
	cd ./../../images/consul && docker build -t outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION)-consul -t outcoldman/docker-splunk-cluster:latest-consul .


deploy:
	docker-compose -f docker-compose.yml up -d
	docker-compose -f docker-compose.yml scale cluster-slave=4 shc-member=3 data-collector-hec=2
	@echo "Use 'docker-compose -f docker-compose.yml -f docker-compose.license-master.yml logs -f cluster-master' to wait for Initialized cluster-master as Cluster Master"
