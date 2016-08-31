SPLUNK_VERSION ?= 6.4.3
DOCKER_REGISTRY ?=
# If you don't want (cannot) delete old volumes, just use SALT to use new one
SALT ?=

setup-clean:
	seq 0 5 | xargs -I @ docker-machine rm -f splunk@
	docker-machine rm -f registry

setup:
	docker-machine create \
		--driver=virtualbox \
		--virtualbox-disk-size=200000 \
		--virtualbox-memory=512 \
		--virtualbox-cpu-count=1 \
		registry
	eval $$(docker-machine env registry) && docker run \
		--name registry \
		--publish 80:5000/tcp \
		--restart=always \
		-d registry:2
	seq 0 5 | xargs -P 6 -I @ bash -c "docker-machine create \
		--driver=virtualbox \
		--virtualbox-disk-size=200000 \
		--virtualbox-memory=1536 \
		--virtualbox-cpu-count=2 \
		--engine-insecure-registry $$(docker-machine ip registry) \
		splunk@"
	(eval $$(docker-machine env splunk0) && docker swarm init --advertise-addr $$(docker-machine ip splunk0))
	seq 3 | xargs -I @ bash -c 'eval $$(docker-machine env splunk@) && docker swarm join --listen-addr $$(docker-machine ip splunk@) $$(docker-machine ip splunk0):2377 --token $$(eval $$(docker-machine env splunk0) && docker swarm  join-token -q worker )' 
	(eval $$(docker-machine env splunk0) && docker network create --driver=overlay splunk)
	seq 3 | xargs -I @ bash -c 'eval $$(docker-machine env splunk0) && docker node update --label-add index=@ splunk@'

setup-add-2:
	seq 4 5 | xargs -I @ bash -c 'eval $$(docker-machine env splunk@) && docker swarm join --listen-addr $$(docker-machine ip splunk@) $$(docker-machine ip splunk0):2377 --token $$(eval $$(docker-machine env splunk0) && docker swarm  join-token -q worker )' 
	seq 4 5 | xargs -I @ bash -c 'eval $$(docker-machine env splunk0) && docker node update --label-add index=@ splunk@'

setup-remove-2:
	-seq 4 5 | xargs -I @ bash -c 'eval $$(docker-machine env splunk@) && docker swarm leave' 
	-seq 4 5 | xargs -I @ bash -c 'eval $$(docker-machine env splunk0) && docker node rm splunk@'

build:
	cd ./../../images/splunk && docker build -t $$(docker-machine ip registry)/outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION) . && docker push $$(docker-machine ip registry)/outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION)
	cd ./../../images/lb && docker build -t $$(docker-machine ip registry)/outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION)-lb . && docker push $$(docker-machine ip registry)/outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION)-lb
	cd ./../../images/consul && docker build -t $$(docker-machine ip registry)/outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION)-consul . && docker push $$(docker-machine ip registry)/outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION)-consul
	echo 'Use `export DOCKER_REGISTRY=$$(docker-machine ip registry)/` to setup Splunk Cluster with custom images'

deploy-consul:
	docker service create \
		--constraint "node.id == $$(docker node ls | grep '*' | awk '{print($$1)}')" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 64m \
		--name consul \
		--mode replicated \
		--container-label splunk.cluster=consul \
		--label splunk.cluster=consul \
		--network splunk \
		--mount "type=volume,source=consul$(SALT),destination=/var/consul" \
		--env CONSUL_DATA_DIR="/var/consul/data" \
		--env CONSUL_DC="dc" \
		--env CONSUL_DOMAIN="splunk" \
		--env CONSUL_CLIENT="127.0.0.1" \
		--env CONSUL_BOOTSTRAP_EXPECT="1" \
		--env CONSUL_JOIN="consul" \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		--env SYSLOG_SERVER=cluster-slave \
		--env SYSLOG_PORT=1514 \
		--env SYSLOG_PROTO=udp \
		$(DOCKER_REGISTRY)outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION)-consul

deploy-lb:
	docker service create \
		--constraint "node.id == $$(docker node ls | grep '*' | awk '{print($$1)}')" \
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
		--publish 8500:8500 \
		--publish 8089:8089 \
		--publish 8088:8088 \
		--env CONSUL_DC="dc" \
		--env CONSUL_HOST="consul" \
		--env CONSUL_DOMAIN="splunk" \
		--env CONSUL_ADVERTISE_INTERFACE=eth2 \
		--env SYSLOG_SERVER=cluster-slave \
		--env SYSLOG_PORT=1514 \
		--env SYSLOG_PROTO=udp \
		$(DOCKER_REGISTRY)outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION)-lb

deploy-cluster-master:
	ls *.lic 1> /dev/null 2>&1;
	docker service create \
		--constraint "node.id == $$(docker node ls | grep '*' | awk '{print($$1)}')" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 512m \
		--name cluster-master \
		--container-label splunk.cluster=cluster-master \
		--label splunk.cluster=cluster-master \
		--network splunk \
		--mount "type=volume,source=cluster-master-etc$(SALT),destination=/opt/splunk/etc" \
		--mount "type=volume,source=cluster-master-var$(SALT),destination=/opt/splunk/var" \
		--env SPLUNK_START_ARGS="--accept-license --answer-yes --no-prompt" \
		--env SPLUNK_ROLES=cluster_master,license_master,shc_deployer,dmc,deployment_server \
		--env INIT_CLUSTERING_PASS_4_SYMM_KEY=clustering-changeme \
		--env INIT_CLUSTERING_REPLICATION_FACTOR=3 \
		--env INIT_CLUSTERING_SEARCH_FACTOR=2 \
		--env INIT_CLUSTERING_CLUSTER_LABEL=cluster \
		--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
		--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
		--env INIT_GENERAL_PASS_4_SYMM_KEY=general-changeme \
		--env INIT_WEB_ENABLED=true \
		--env INIT_KVSTORE_ENABLED=false \
		--env INIT_WAIT_LICENSE=true \
		--env INIT_SHCLUSTERING_PASS_4_SYMM_KEY=shclustering-changeme \
		--env INIT_SHCLUSTERING_SHCLUSTER_LABEL=shcluster \
		--env INIT_DEPLOYMENT_PASS_4_SYMM_KEY=deployment-changeme \
		--env INIT_DEPLOYMENT_REQUIRE_AUTHENTICATION=true \
		--env INIT_DEPLOYMENT_CROSS_SERVER_CHECKSUM=true \
		--env INIT_DEPLOYMENT_SERVER_PUBLIC=true \
		--env INIT_ENABLE_HTTP_EVENT_COLLECTOR=true \
		--env INIT_HTTP_EVENT_COLLECTOR_TOKEN=EF211A51-D6AC-4045-8CD6-F730939AC518 \
		--env INIT_SERVERCLASS_HTTP_EVENT_COLLECTOR=data-collector-hec \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$(DOCKER_REGISTRY)outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION)
	while [[ "$$(docker ps -qa --filter=label=com.docker.swarm.service.name=cluster-master)" == "" ]]; do sleep 1; done
	ls *.lic | xargs -I @ docker cp @ $$(docker ps -qa --filter=label=com.docker.swarm.service.name=cluster-master):/opt/splunk-deployment/licenses/

deploy-shc-member:
	for number in $(shell seq 3); do \
		docker service create \
			--constraint "node.labels.index == $${number}" \
			--name shc-member-0$${number} \
			--mode replicated \
			--replicas 1 \
			--reserve-memory 512m \
			--container-label splunk.cluster=shc-member \
			--label splunk.cluster=shc-member \
			--network splunk \
			--mount "type=volume,source=shc-member-0$${number}-etc$(SALT),destination=/opt/splunk/etc" \
			--mount "type=volume,source=shc-member-0$${number}-var$(SALT),destination=/opt/splunk/var" \
			--env SPLUNK_START_ARGS="--accept-license --answer-yes --no-prompt" \
			--env SPLUNK_ROLES=shc_member,shc_deployer_client,license_slave,cluster_searchhead \
			--env INIT_SHCLUSTERING_PASS_4_SYMM_KEY=shclustering-changeme \
			--env INIT_SHCLUSTERING_SHCDEPLOYER=https://cluster-master:8089 \
			--env INIT_SHCLUSTERING_REPLICATION_FACTOR=3 \
			--env INIT_SHCLUSTERING_SHCLUSTER_LABEL=shcluster \
			--env INIT_GENERAL_PASS_4_SYMM_KEY=general-changeme \
			--env INIT_LICENSE_MASTER=https://cluster-master:8089 \
			--env INIT_CLUSTERING_PASS_4_SYMM_KEY=clustering-changeme \
			--env INIT_CLUSTERING_CLUSTER_MASTER=https://cluster-master:8089 \
			--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
			--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
			--env INIT_SHCLUSTER_AUTOBOOTSTRAP=3 \
			--env INIT_SHCLUSTERING_HOSTNAME=shc-member-0$${number} \
			--env CONSUL_HOST=consul \
			--env CONSUL_DC=dc \
			--env CONSUL_DOMAIN=splunk \
			--env CONSUL_ADVERTISE_INTERFACE=eth0 \
			$(DOCKER_REGISTRY)outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION); \
	done

deploy-cluster-slave:
	docker service create \
		--constraint "node.role != manager" \
		--name cluster-slave \
		--mode global \
		--reserve-memory 512m \
		--container-label splunk.cluster=cluster-slave \
		--label splunk.cluster=cluster-slave \
		--network splunk \
		--mount "type=volume,source=cluster-slave-etc$(SALT),destination=/opt/splunk/etc" \
		--mount "type=volume,source=cluster-slave-var$(SALT),destination=/opt/splunk/var" \
		--env SPLUNK_START_ARGS="--accept-license --answer-yes --no-prompt" \
		--env SPLUNK_ROLES=cluster_slave,license_slave,deployment_client,data_collector \
		--env INIT_GENERAL_PASS_4_SYMM_KEY=general-changeme \
		--env INIT_LICENSE_MASTER=https://cluster-master:8089 \
		--env INIT_CLUSTERING_PASS_4_SYMM_KEY=clustering-changeme \
		--env INIT_CLUSTERING_CLUSTER_MASTER=https://cluster-master:8089 \
		--env INIT_DEPLOYMENT_PASS_4_SYMM_KEY=deployment-changeme \
		--env INIT_DEPLOYMENT_CLIENT_NAME=data-collector-hec \
		--env INIT_DEPLOYMENT_CLIENT_DEPLOYMENT_SERVER=cluster-master:8089 \
		--env INIT_REGISTER_PUBLIC_HTTP_EVENT_COLLECTOR=true \
		--env INIT_ADD_UDP_PORT=1514 \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$(DOCKER_REGISTRY)outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION); \

deploy: deploy-consul deploy-cluster-master deploy-shc-member deploy-cluster-slave deploy-lb

demo-add-peers:
	seq 3 | xargs -I @ docker exec $$(docker ps -qa --filter=label=com.docker.swarm.service.name=cluster-master) entrypoint.sh splunk add search-server shc-member-0@:8089 -remoteUsername admin -remotePassword changed -auth admin:changeme

demo-add-2-shc:
	for number in $(shell seq 4 5); do \
		docker service create \
			--constraint "node.labels.index == $${number}" \
			--name shc-member-0$${number} \
			--mode replicated \
			--replicas 1 \
			--reserve-memory 512m \
			--container-label splunk.cluster=shc-member \
			--label splunk.cluster=shc-member \
			--network splunk \
			--mount "type=volume,source=shc-member-0$${number}-etc$(SALT),destination=/opt/splunk/etc" \
			--mount "type=volume,source=shc-member-0$${number}-var$(SALT),destination=/opt/splunk/var" \
			--env SPLUNK_START_ARGS="--accept-license --answer-yes --no-prompt" \
			--env SPLUNK_ROLES=shc_member,shc_deployer_client,license_slave,cluster_searchhead \
			--env INIT_SHCLUSTERING_PASS_4_SYMM_KEY=shclustering-changeme \
			--env INIT_SHCLUSTERING_SHCDEPLOYER=https://cluster-master:8089 \
			--env INIT_SHCLUSTERING_REPLICATION_FACTOR=3 \
			--env INIT_SHCLUSTERING_SHCLUSTER_LABEL=shcluster \
			--env INIT_GENERAL_PASS_4_SYMM_KEY=general-changeme \
			--env INIT_LICENSE_MASTER=https://cluster-master:8089 \
			--env INIT_CLUSTERING_PASS_4_SYMM_KEY=clustering-changeme \
			--env INIT_CLUSTERING_CLUSTER_MASTER=https://cluster-master:8089 \
			--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
			--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
			--env INIT_SHCLUSTER_AUTOBOOTSTRAP=3 \
			--env INIT_SHCLUSTERING_HOSTNAME=shc-member-0$${number} \
			--env CONSUL_HOST=consul \
			--env CONSUL_DC=dc \
			--env CONSUL_DOMAIN=splunk \
			--env CONSUL_ADVERTISE_INTERFACE=eth0 \
			$(DOCKER_REGISTRY)outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION); \
	done

demo-add-more-peers:
	seq 4 5 | xargs -I @ docker exec $$(docker ps -qa --filter=label=com.docker.swarm.service.name=cluster-master) entrypoint.sh splunk add search-server shc-member-0@:8089 -remoteUsername admin -remotePassword changed -auth admin:changeme

clean:
	-docker service rm consul cluster-master lb cluster-slave
	-seq 3 | xargs -I @ docker service rm cluster-slave-0@
	-seq 4 5 | xargs -I @ docker service rm cluster-slave-0@
	-seq 3 | xargs -I @ docker service rm shc-member-0@
	-seq 4 5 | xargs -I @ docker service rm shc-member-0@

clean-volumes:
	-seq 0 5 | xargs -I @ bash -c 'eval $$(docker-machine env splunk@); docker kill $$(docker ps -q); docker rm -v $$(docker ps -aq); docker volume rm $$(docker volume ls -q)'

clean-all: clean clean-volumes

upgrade:
	@echo "Updating first consul"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION)-consul consul-first
	@sleep 10
	@echo "Updating consul cluster"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION)-consul consul
	@sleep 20
	@echo "Updating lb"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION)-lb lb
	@echo "Updating cluster-master"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION) cluster-master
	@echo "Updating dmc"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION) dmc
	@echo "Updating deployment-server"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION) deployment-server
	@echo "Updating data-collector-hec"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION) data-collector-hec
	@echo "Updating shc-member"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION) shc-member
	@echo "Updating cluster-slave"
	docker service update --image $(DOCKER_REGISTRY)outcoldman/docker-splunk-cluster:$(SPLUNK_VERSION) cluster-slave
