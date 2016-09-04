# With license master

export SPLUNK_CLUSTER_VERSION ?= 6.4.3
export SPLUNK_CLUSTER_DOCKER_IMAGE_PATH ?= ${USER}

clean-lm:
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml kill
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml rm -v -f

bundle:
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml bundle

build-lm: build

push-lm: push

deploy-lm:
	#docker-compose -f docker-compose.yml -f docker-compose.license-master.yml pull
	@echo "Verifying that at least one *.lic file exist"
	ls *.lic 1> /dev/null 2>&1;
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml up -d cluster-master
	ls *.lic | xargs -I @ docker cp @ $$(docker ps -qa --filter=label=splunk.cluster=cluster-master):/opt/
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml up -d
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml scale cluster-slave=3
	@echo "Use 'docker-compose -f docker-compose.yml -f docker-compose.license-master.yml logs -f cluster-master' to wait for Initialized cluster-master as Cluster Master"

# Without license master

clean:
	docker-compose -f docker-compose.yml kill
	docker-compose -f docker-compose.yml rm -v -f

build:
	cd ./../../splunk-cluster && docker build --build-arg SPLUNK_VERSION=$(SPLUNK_CLUSTER_VERSION) -t $(SPLUNK_CLUSTER_DOCKER_IMAGE_PATH)/splunk-cluster:$(SPLUNK_CLUSTER_VERSION) -t $(SPLUNK_CLUSTER_DOCKER_IMAGE_PATH)/splunk-cluster:latest .

push: build
	docker push $(SPLUNK_CLUSTER_DOCKER_IMAGE_PATH)/splunk-cluster:$(SPLUNK_CLUSTER_VERSION)
	docker push $(SPLUNK_CLUSTER_DOCKER_IMAGE_PATH)/splunk-cluster:latest

deploy:
	docker-compose -f docker-compose.yml -f docker-compose.license-master.yml pull
	docker-compose -f docker-compose.yml up -d
	docker-compose -f docker-compose.yml scale cluster-slave=3
	@echo "Use 'docker-compose -f docker-compose.yml -f docker-compose.license-master.yml logs -f cluster-master' to wait for Initialized cluster-master as Cluster Master"
