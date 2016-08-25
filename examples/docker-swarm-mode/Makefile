SPLUNK_VERSION ?= 6.4.3
DOCKER_REGISTRY ?=

setup-clean:
	docker-machine rm -f registry splunk1 splunk2 splunk3

setup:
	docker-machine create \
		--driver=virtualbox \
		--virtualbox-disk-size=200000 \
		--virtualbox-memory=512 \
		--virtualbox-cpu-count=1 \
		--virtualbox-boot2docker-url=https://github.com/boot2docker/boot2docker/releases/download/v1.12.1-rc1/boot2docker.iso \
		registry
	eval $$(docker-machine env registry) && docker run \
		--name registry \
		--publish 80:5000/tcp \
		--restart=always \
		-d registry:2
	docker-machine create \
		--driver=virtualbox \
		--virtualbox-disk-size=200000 \
		--virtualbox-memory=4096 \
		--virtualbox-cpu-count=2 \
		--virtualbox-boot2docker-url=https://github.com/boot2docker/boot2docker/releases/download/v1.12.1-rc1/boot2docker.iso \
		--engine-insecure-registry $$(docker-machine ip registry) \
		splunk1
	docker-machine create \
		--driver=virtualbox \
		--virtualbox-disk-size=200000 \
		--virtualbox-memory=3072 \
		--virtualbox-cpu-count=2 \
		--virtualbox-boot2docker-url=https://github.com/boot2docker/boot2docker/releases/download/v1.12.1-rc1/boot2docker.iso \
		--engine-insecure-registry $$(docker-machine ip registry) \
		splunk2
	docker-machine create \
		--driver=virtualbox \
		--virtualbox-disk-size=200000 \
		--virtualbox-memory=3072 \
		--virtualbox-cpu-count=2 \
		--virtualbox-boot2docker-url=https://github.com/boot2docker/boot2docker/releases/download/v1.12.1-rc1/boot2docker.iso \
		--engine-insecure-registry $$(docker-machine ip registry) \
		splunk3
	(eval $$(docker-machine env splunk1) && docker swarm init --advertise-addr $$(docker-machine ip splunk1))
	(eval $$(docker-machine env splunk2) && docker swarm join --listen-addr $$(docker-machine ip splunk2) $$(docker-machine ip splunk1):2377 --token $$(eval $$(docker-machine env splunk1) && docker swarm  join-token -q worker ) )
	(eval $$(docker-machine env splunk3) && docker swarm join --listen-addr $$(docker-machine ip splunk3) $$(docker-machine ip splunk1):2377 --token $$(eval $$(docker-machine env splunk1) && docker swarm  join-token -q worker ) )
	(eval $$(docker-machine env splunk1) && docker network create --driver=overlay splunk)
	(eval $$(docker-machine env splunk1) && docker node update --label-add index=1 splunk1 && docker node update --label-add index=2 splunk2 && docker node update --label-add index=3 splunk3)

build:
	cd ./../../images/splunk && docker build -t $(docker-machine ip registry)/outcoldman/splunk-cluster:$(SPLUNK_VERSION) . && docker push $$(docker-machine ip registry)/outcoldman/splunk-cluster:$(SPLUNK_VERSION)
	cd ./../../images/lb && docker build -t $$(docker-machine ip registry)/outcoldman/splunk-cluster:$(SPLUNK_VERSION)-lb . && docker push $$(docker-machine ip registry)/outcoldman/splunk-cluster:$(SPLUNK_VERSION)-lb
	cd ./../../images/consul && docker build -t $$(docker-machine ip registry)/outcoldman/splunk-cluster:$(SPLUNK_VERSION)-consul . && docker push $$(docker-machine ip registry)/outcoldman/splunk-cluster:$(SPLUNK_VERSION)-consul
	echo 'Use `DOCKER_REGISTRY=$$(docker-machine ip registry)/` to setup Splunk Cluster with custom images'

deploy-consul:
	docker service create \
		--constraint "node.labels.index == 1" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 64m \
		--name consul \
		--mode replicated \
		--container-label splunk.cluster=consul \
		--label splunk.cluster=consul \
		--network splunk \
		--mount "type=volume,source=consul,destination=/var/consul" \
		--env CONSUL_DATA_DIR="/var/consul/data" \
		--env CONSUL_DC="dc" \
		--env CONSUL_DOMAIN="splunk" \
		--env CONSUL_CLIENT="127.0.0.1" \
		--env CONSUL_BOOTSTRAP_EXPECT="3" \
		--env CONSUL_JOIN="consul" \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		--env SYSLOG_SERVER=data-collector-internal \
		--env SYSLOG_PORT=1514 \
		--env SYSLOG_PROTO=udp \
		$(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION)-consul
	seq 2 3 | xargs -R 10 -I @ docker service create \
		--constraint "node.labels.index == @" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 64m \
		--name consul@ \
		--mode replicated \
		--label splunk.cluster=consul \
		--network splunk \
		--mount "type=volume,source=consul-@,destination=/var/consul" \
		--env CONSUL_DATA_DIR="/var/consul/data" \
		--env CONSUL_DC="dc" \
		--env CONSUL_DOMAIN="splunk" \
		--env CONSUL_CLIENT="127.0.0.1" \
		--env CONSUL_BOOTSTRAP_EXPECT="3" \
		--env CONSUL_JOIN="consul" \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		--env SYSLOG_SERVER=data-collector-internal \
		--env SYSLOG_PORT=1514 \
		--env SYSLOG_PROTO=udp \
		$(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION)-consul

deploy-data-collector-internal:
	docker service create \
		--constraint "node.labels.index == 1" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 128m \
		--name data-collector-internal \
		--container-label splunk.cluster=data-collector-internal \
		--label splunk.cluster=data-collector-internal \
		--network splunk \
		--mount "type=volume,source=data-collector-internal-etc,destination=/opt/splunk/etc" \
		--mount "type=volume,source=data-collector-internal-var,destination=/opt/splunk/var" \
		--env SPLUNK_START_ARGS="--accept-license --answer-yes --no-prompt" \
		--env SPLUNK_ROLES=data_collector,deployment_client \
		--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
		--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
		--env INIT_ADD_UDP_PORT=1514 \
		--env INIT_DEPLOYMENT_PASS_4_SYMM_KEY=deployment-changeme \
		--env INIT_DEPLOYMENT_CLIENT_NAME=data-collector-internal \
		--env INIT_DEPLOYMENT_CLIENT_DEPLOYMENT_SERVER=deployment-server:8089 \
		--env INIT_SERVER_GENERAL_SERVERNAME=data-collector-internal \
		--env INIT_INPUTS_DEFAULT_HOST=data-collector-internal \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION)

deploy-lb:
	docker service create \
		--constraint "node.labels.index == 1" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 256m \
		--name lb \
		--mode replicated \
		--container-label splunk.cluster=lb \
		--label splunk.cluster=lb \
		--network splunk \
		--publish 8000:8000 \
		--publish 8010:8010 \
		--publish 8020:8020 \
		--publish 8030:8030 \
		--publish 8040:8040 \
		--publish 8500:8500 \
		--publish 8089:8089 \
		--publish 8088:8088 \
		--env CONSUL_DC="dc" \
		--env CONSUL_HOST="consul" \
		--env CONSUL_DOMAIN="splunk" \
		--env CONSUL_ADVERTISE_INTERFACE=eth2 \
		--env SYSLOG_SERVER=data-collector-internal \
		--env SYSLOG_PORT=1514 \
		--env SYSLOG_PROTO=udp \
		$(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION)-lb

deploy-license-master:
	ls *.lic 1> /dev/null 2>&1;
	docker service create \
		--constraint "node.labels.index == 1" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 256m \
		--name license-master \
		--container-label splunk.cluster=license-master \
		--label splunk.cluster=license-master \
		--network splunk \
		--mount "type=volume,source=license-master-etc,destination=/opt/splunk/etc" \
		--mount "type=volume,source=license-master-var,destination=/opt/splunk/var" \
		--env SPLUNK_START_ARGS="--accept-license --answer-yes --no-prompt" \
		--env SPLUNK_ROLES=license_master \
		--env INIT_GENERAL_PASS_4_SYMM_KEY=general-changeme \
		--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
		--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
		--env INIT_WEB_ENABLED=true \
		--env INIT_WAIT_LICENSE=true \
		--env INIT_SERVER_GENERAL_SERVERNAME=license-master \
		--env INIT_INPUTS_DEFAULT_HOST=license-master \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION)
	while [[ "$$(docker ps -qa --filter=label=com.docker.swarm.service.name=license-master)" == "" ]]; do sleep 1; done
	ls *.lic | xargs -I @ docker cp @ $$(docker ps -qa --filter=label=com.docker.swarm.service.name=license-master):/opt/splunk-deployment/licenses/

deploy-cluster-master:
	docker service create \
		--constraint "node.labels.index == 1" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 256m \
		--name cluster-master \
		--container-label splunk.cluster=cluster-master \
		--label splunk.cluster=cluster-master \
		--network splunk \
		--mount "type=volume,source=cluster-master-etc,destination=/opt/splunk/etc" \
		--mount "type=volume,source=cluster-master-var,destination=/opt/splunk/var" \
		--env SPLUNK_START_ARGS="--accept-license --answer-yes --no-prompt" \
		--env SPLUNK_ROLES=cluster_master,license_slave \
		--env INIT_CLUSTERING_PASS_4_SYMM_KEY=clustering-changeme \
		--env INIT_CLUSTERING_REPLICATION_FACTOR=1 \
		--env INIT_CLUSTERING_SEARCH_FACTOR=1 \
		--env INIT_CLUSTERING_CLUSTER_LABEL=cluster \
		--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
		--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
		--env INIT_GENERAL_PASS_4_SYMM_KEY=general-changeme \
		--env INIT_LICENSE_MASTER=https://license-master:8089 \
		--env INIT_WEB_ENABLED=true \
		--env INIT_SERVER_GENERAL_SERVERNAME=cluster-master \
		--env INIT_INPUTS_DEFAULT_HOST=cluster-master \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION)

deploy-shc-deployer:
	docker service create \
		--constraint "node.labels.index == 1" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 256m \
		--name shc-deployer \
		--container-label splunk.cluster=shc-deployer \
		--label splunk.cluster=shc-deployer \
		--network splunk \
		--mount "type=volume,source=shc-deployer-etc,destination=/opt/splunk/etc" \
		--mount "type=volume,source=shc-deployer-var,destination=/opt/splunk/var" \
		--env SPLUNK_START_ARGS="--accept-license --answer-yes --no-prompt" \
		--env SPLUNK_ROLES=shc_deployer \
		--env INIT_SHCLUSTERING_PASS_4_SYMM_KEY=shclustering-changeme \
		--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
		--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION)

deploy-shc-member:
	for number in $(shell seq 3); do \
		host_n=$$(echo $${number}%3+1 | bc); \
		docker service create \
			--constraint "node.labels.index == $${host_n}" \
			--name shc-member-0$${number} \
			--mode replicated \
			--replicas 1 \
			--reserve-memory 512m \
			--container-label splunk.cluster=shc-member \
			--label splunk.cluster=shc-member \
			--network splunk \
			--mount "type=volume,source=shc-member-0$${number}-etc,destination=/opt/splunk/etc" \
			--mount "type=volume,source=shc-member-0$${number}-var,destination=/opt/splunk/var" \
			--env SPLUNK_START_ARGS="--accept-license --answer-yes --no-prompt" \
			--env SPLUNK_ROLES=shc_member,shc_deployer_client,license_slave,cluster_searchhead \
			--env INIT_SHCLUSTERING_PASS_4_SYMM_KEY=shclustering-changeme \
			--env INIT_SHCLUSTERING_SHCDEPLOYER=https://shc-deployer:8089 \
			--env INIT_SHCLUSTERING_REPLICATION_FACTOR=3 \
			--env INIT_SHCLUSTERING_SHCLUSTER_LABEL=shcluster \
			--env INIT_GENERAL_PASS_4_SYMM_KEY=general-changeme \
			--env INIT_LICENSE_MASTER=https://license-master:8089 \
			--env INIT_CLUSTERING_PASS_4_SYMM_KEY=clustering-changeme \
			--env INIT_CLUSTERING_CLUSTER_MASTER=https://cluster-master:8089 \
			--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
			--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
			--env INIT_SHCLUSTER_AUTOBOOTSTRAP=3 \
			--env INIT_SHCLUSTERING_HOSTNAME=shc-member-0$${number} \
			--env INIT_SERVER_GENERAL_SERVERNAME=shc-member-0$${number} \
			--env INIT_INPUTS_DEFAULT_HOST=shc-member-0$${number} \
			--env CONSUL_HOST=consul \
			--env CONSUL_DC=dc \
			--env CONSUL_DOMAIN=splunk \
			--env CONSUL_ADVERTISE_INTERFACE=eth0 \
			$(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION); \
	done

deploy-cluster-slave:
	for number in $(shell seq 4); do \
		host_n=$$(echo $${number}%3+1 | bc); \
		docker service create \
			--constraint "node.labels.index == $${host_n}" \
			--name cluster-slave-0$${number} \
			--mode replicated \
			--replicas 1 \
			--reserve-memory 512m \
			--container-label splunk.cluster=cluster-slave \
			--label splunk.cluster=cluster-slave \
			--network splunk \
			--mount "type=volume,source=cluster-slave-0$${number}-etc,destination=/opt/splunk/etc" \
			--mount "type=volume,source=cluster-slave-0$${number}-var,destination=/opt/splunk/var" \
			--env SPLUNK_START_ARGS="--accept-license --answer-yes --no-prompt" \
			--env SPLUNK_ROLES=cluster_slave,license_slave \
			--env INIT_GENERAL_PASS_4_SYMM_KEY=general-changeme \
			--env INIT_LICENSE_MASTER=https://license-master:8089 \
			--env INIT_CLUSTERING_PASS_4_SYMM_KEY=clustering-changeme \
			--env INIT_CLUSTERING_CLUSTER_MASTER=https://cluster-master:8089 \
			--env INIT_CLUSTERING_REGISTER_FORWARDER_ADDRESS=cluster-slave-0$${number} \
			--env INIT_CLUSTERING_REGISTER_SEARCH_ADDRESS=cluster-slave-0$${number} \
			--env INIT_CLUSTERING_REGISTER_REPLICATION_ADDRESS=cluster-slave-0$${number} \
			--env INIT_SERVER_GENERAL_SERVERNAME=cluster-slave-0$${number} \
			--env INIT_INPUTS_DEFAULT_HOST=cluster-slave-0$${number} \
			--env CONSUL_HOST=consul \
			--env CONSUL_DC=dc \
			--env CONSUL_DOMAIN=splunk \
			--env CONSUL_ADVERTISE_INTERFACE=eth0 \
			$(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION); \
	done

deploy-dmc:
	docker service create \
		--constraint "node.labels.index == 1" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 512m \
		--name dmc \
		--container-label splunk.cluster=dmc \
		--label splunk.cluster=dmc \
		--network splunk \
		--mount "type=volume,source=dmc-etc,destination=/opt/splunk/etc" \
		--mount "type=volume,source=dmc-var,destination=/opt/splunk/var" \
		--env SPLUNK_START_ARGS="--accept-license --answer-yes --no-prompt" \
		--env SPLUNK_ROLES=license_slave,cluster_searchhead,dmc \
		--env INIT_CLUSTERING_PASS_4_SYMM_KEY=clustering-changeme \
		--env INIT_CLUSTERING_CLUSTER_MASTER=https://cluster-master:8089 \
		--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
		--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
		--env INIT_GENERAL_PASS_4_SYMM_KEY=general-changeme \
		--env INIT_LICENSE_MASTER=https://license-master:8089 \
		--env INIT_KVSTORE_ENABLED=false \
		--env INIT_SERVER_GENERAL_SERVERNAME=dmc \
		--env INIT_INPUTS_DEFAULT_HOST=dmc \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION)

deploy-deployment-server:
	docker service create \
		--constraint "node.labels.index == 1" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 256m \
		--name deployment-server \
		--container-label splunk.cluster=deployment-server \
		--label splunk.cluster=deployment-server \
		--network splunk \
		--mount "type=volume,source=deployment-server-etc,destination=/opt/splunk/etc" \
		--mount "type=volume,source=deployment-server-var,destination=/opt/splunk/var" \
		--env SPLUNK_START_ARGS="--accept-license --answer-yes --no-prompt" \
		--env SPLUNK_ROLES=deployment_server \
		--env INIT_DEPLOYMENT_PASS_4_SYMM_KEY=deployment-changeme \
		--env INIT_DEPLOYMENT_REQUIRE_AUTHENTICATION=true \
		--env INIT_DEPLOYMENT_CROSS_SERVER_CHECKSUM=true \
		--env INIT_DEPLOYMENT_SERVER_PUBLIC=true \
		--env INIT_ENABLE_HTTP_EVENT_COLLECTOR=true \
		--env INIT_HTTP_EVENT_COLLECTOR_TOKEN=EF211A51-D6AC-4045-8CD6-F730939AC518 \
		--env INIT_SERVERCLASS_HTTP_EVENT_COLLECTOR=data-collector-hec \
		--env INIT_SERVER_GENERAL_SERVERNAME=deployment-server \
		--env INIT_INPUTS_DEFAULT_HOST=deployment-server \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION)

deploy-data-collector-hec:
	docker service create \
		--mode replicated \
		--replicas 2 \
		--reserve-memory 256m \
		--name data-collector-hec \
		--container-label splunk.cluster=data-collector-hec \
		--label splunk.cluster=data-collector-hec \
		--network splunk \
		--update-parallelism=1 \
		--update-delay 30s \
		--env SPLUNK_START_ARGS="--accept-license --answer-yes --no-prompt" \
		--env SPLUNK_ROLES=data_collector,deployment_client \
		--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
		--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
		--env INIT_DEPLOYMENT_PASS_4_SYMM_KEY=deployment-changeme \
		--env INIT_DEPLOYMENT_CLIENT_NAME=data-collector-hec \
		--env INIT_DEPLOYMENT_CLIENT_DEPLOYMENT_SERVER=deployment-server:8089 \
		--env INIT_REGISTER_PUBLIC_HTTP_EVENT_COLLECTOR=true \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION)

deploy: deploy-consul deploy-license-master deploy-cluster-master deploy-shc-deployer deploy-shc-member deploy-cluster-slave deploy-dmc deploy-data-collector-hec deploy-data-collector-internal deploy-lb deploy-deployment-server

clean:
	-docker service rm consul license-master cluster-master shc-deployer dmc data-collector-hec data-collector-internal lb deployment-server
	-seq 2 3 | xargs -I @ docker service rm consul@
	-seq 3 | xargs -I @ docker service rm shc-member-0@
	-seq 4 | xargs -I @ docker service rm cluster-slave-0@
	-(eval $$(docker-machine env splunk1); docker kill $$(docker ps -q); docker rm -v $$(docker ps -aq); docker volume rm $$(docker volume ls -q))
	-(eval $$(docker-machine env splunk2); docker kill $$(docker ps -q); docker rm -v $$(docker ps -aq); docker volume rm $$(docker volume ls -q))
	-(eval $$(docker-machine env splunk3); docker kill $$(docker ps -q); docker rm -v $$(docker ps -aq); docker volume rm $$(docker volume ls -q))

upgrade:
	@echo "Updating first consul"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION)-consul consul-first
	@sleep 10
	@echo "Updating consul cluster"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION)-consul consul
	@sleep 20
	@echo "Updating data-collector-internal"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION) data-collector-internal
	@echo "Updating lb"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION)-lb lb
	@echo "Updating license-master"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION) license-master
	@echo "Updating cluster-master"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION) cluster-master
	@echo "Updating shc-deployer"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION) shc-deployer
	@echo "Updating dmc"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION) dmc
	@echo "Updating deployment-server"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION) deployment-server
	@echo "Updating data-collector-hec"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION) data-collector-hec
	@echo "Updating shc-member"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION) shc-member
	@echo "Updating cluster-slave"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/splunk-cluster:$(SPLUNK_VERSION) cluster-slave
