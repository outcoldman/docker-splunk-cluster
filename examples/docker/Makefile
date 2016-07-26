# With license master

clean-lm:
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml kill
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml rm -v -f

build-lm: build

deploy-lm:
	test -f *.lic
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml up -d license-master
	docker cp *.lic $$(docker ps -qa --filter=label=splunk.cluster=license-master):/opt/splunk-deployment/licenses/
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml up -d
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml scale cluster-slave=4 shc-member=3 data-collector-hec=2
	@echo "Use 'docker-compose -f docker-compose.yml -f docker-compose.license-master.yml logs -f cluster-master' to wait for Initialized cluster-master as Cluster Master"

# Without license master

clean:
	docker-compose -f docker-compose.yml kill
	docker-compose -f docker-compose.yml rm -v -f

build:
	cd ./../../images/splunk && docker build -t outcoldman/splunk-cluster:6.4.2 .
	cd ./../../images/lb && docker build -t outcoldman/splunk-cluster:6.4.2-lb .
	cd ./../../images/consul && docker build -t outcoldman/splunk-cluster:6.4.2-consul .


deploy:
	docker-compose -f docker-compose.yml up -d
	docker-compose -f docker-compose.yml scale cluster-slave=4 shc-member=3 data-collector-hec=2
	@echo "Use 'docker-compose -f docker-compose.yml -f docker-compose.license-master.yml logs -f cluster-master' to wait for Initialized cluster-master as Cluster Master"
