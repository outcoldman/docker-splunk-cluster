setup-clean:
	docker-machine rm -f registry splunk1 splunk2 splunk3

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
		-d registry:2
	docker-machine create \
		--driver=virtualbox \
		--virtualbox-disk-size=200000 \
		--virtualbox-memory=4096 \
		--virtualbox-cpu-count=2 \
		--engine-insecure-registry $$(docker-machine ip registry) \
		splunk1
	docker-machine create \
		--driver=virtualbox \
		--virtualbox-disk-size=200000 \
		--virtualbox-memory=3072 \
		--virtualbox-cpu-count=2 \
		--engine-insecure-registry $$(docker-machine ip registry) \
		splunk2
	docker-machine create \
		--driver=virtualbox \
		--virtualbox-disk-size=200000 \
		--virtualbox-memory=3072 \
		--virtualbox-cpu-count=2 \
		--engine-insecure-registry $$(docker-machine ip registry) \
		splunk3
	(eval $$(docker-machine env splunk1) && docker swarm init --advertise-addr $$(docker-machine ip splunk1))
	(eval $$(docker-machine env splunk2) && docker swarm join --listen-addr $$(docker-machine ip splunk2) $$(docker-machine ip splunk1):2377 --token $$(eval $$(docker-machine env splunk1) && docker swarm  join-token -q worker ) )
	(eval $$(docker-machine env splunk3) && docker swarm join --listen-addr $$(docker-machine ip splunk3) $$(docker-machine ip splunk1):2377 --token $$(eval $$(docker-machine env splunk1) && docker swarm  join-token -q worker ) )
	eval $$(docker-machine env splunk1)
	docker network create --driver=overlay splunk

build:
	cd ./../../images/splunk && docker build -t $$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2 . && docker push $$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2
	cd ./../../images/lb && docker build -t $$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2-lb . && docker push $$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2-lb
	cd ./../../images/consul && docker build -t $$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2-consul . && docker push $$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2-consul

deploy-consul:
	docker service create \
		--constraint "node.role == manager" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 64m \
		--name consul-first \
		--mode replicated \
		--container-label splunk.cluster=consul \
		--label splunk.cluster=consul \
		--network splunk \
		--env CONSUL_DATA_DIR="/consul/data" \
		--env CONSUL_DC="dc" \
		--env CONSUL_DOMAIN="splunk" \
		--env CONSUL_CLIENT="127.0.0.1" \
		--env CONSUL_BOOTSTRAP_EXPECT="3" \
		--env CONSUL_JOIN="consul" \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		--env SYSLOG_SERVER=data-collector-internal \
		--env SYSLOG_PORT=1514 \
		--env SYSLOG_PROTO=udp \
		$$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2-consul
	docker service create \
		--constraint "node.role != manager" \
		--mode replicated \
		--replicas 2 \
		--reserve-memory 64m \
		--name consul \
		--mode replicated \
		--label splunk.cluster=consul \
		--network splunk \
		--env CONSUL_DATA_DIR="/consul/data" \
		--env CONSUL_DC="dc" \
		--env CONSUL_DOMAIN="splunk" \
		--env CONSUL_CLIENT="127.0.0.1" \
		--env CONSUL_BOOTSTRAP_EXPECT="3" \
		--env CONSUL_JOIN="consul-first" \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		--env SYSLOG_SERVER=data-collector-internal \
		--env SYSLOG_PORT=1514 \
		--env SYSLOG_PROTO=udp \
		$$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2-consul

deploy-data-collector-internal:
	docker service create \
		--constraint "node.role == manager" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 128m \
		--name data-collector-internal \
		--container-label splunk.cluster=data-collector-internal \
		--label splunk.cluster=data-collector-internal \
		--network splunk \
		--env SPLUNK_START_ARGS=--accept-license \
		--env SPLUNK_ROLES=data_collector,deployment_client \
		--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
		--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
		--env INIT_ADD_UDP_PORT=1514 \
		--env INIT_DEPLOYMENT_PASS_4_SYMM_KEY=deployment-changeme \
		--env INIT_DEPLOYMENT_CLIENT_NAME=data-collector-internal \
		--env INIT_DEPLOYMENT_CLIENT_DEPLOYMENT_SERVER=deployment-server:8089 \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2

deploy-lb:
	docker service create \
		--constraint "node.role == manager" \
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
		$$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2-lb

deploy-license-master:
	ls *.lic 1> /dev/null 2>&1;
	docker service create \
		--constraint "node.role == manager" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 256m \
		--name license-master \
		--container-label splunk.cluster=license-master \
		--label splunk.cluster=license-master \
		--network splunk \
		--env SPLUNK_START_ARGS=--accept-license \
		--env SPLUNK_ROLES=license_master \
		--env INIT_GENERAL_PASS_4_SYMM_KEY=general-changeme \
		--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
		--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
		--env INIT_WEB_ENABLED=true \
		--env INIT_WAIT_LICENSE=true \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2
	while [[ "$$(docker ps -qa --filter=label=com.docker.swarm.service.name=license-master)" == "" ]]; do sleep 1; done
	ls *.lic | xargs -I @ docker cp @ $$(docker ps -qa --filter=label=com.docker.swarm.service.name=license-master):/opt/splunk-deployment/licenses/

deploy-cluster-master:
	docker service create \
		--constraint "node.role == manager" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 256m \
		--name cluster-master \
		--container-label splunk.cluster=cluster-master \
		--label splunk.cluster=cluster-master \
		--network splunk \
		--env SPLUNK_START_ARGS=--accept-license \
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
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2

deploy-shc-deployer:
	docker service create \
		--constraint "node.role == manager" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 256m \
		--name shc-deployer \
		--container-label splunk.cluster=shc-deployer \
		--label splunk.cluster=shc-deployer \
		--network splunk \
		--env SPLUNK_START_ARGS=--accept-license \
		--env SPLUNK_ROLES=shc_deployer \
		--env INIT_SHCLUSTERING_PASS_4_SYMM_KEY=shclustering-changeme \
		--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
		--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2

deploy-shc-member:
	docker service create \
		--mode replicated \
		--replicas 3 \
		--reserve-memory 512m \
		--name shc-member \
		--container-label splunk.cluster=shc-member \
		--label splunk.cluster=shc-member \
		--network splunk \
		--env SPLUNK_START_ARGS=--accept-license \
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
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2

deploy-cluster-slave:
	docker service create \
		--mode replicated \
		--replicas 4 \
		--reserve-memory 512m \
		--name cluster-slave \
		--container-label splunk.cluster=cluster-slave \
		--label splunk.cluster=cluster-slave \
		--network splunk \
		--env SPLUNK_START_ARGS=--accept-license \
		--env SPLUNK_ROLES=cluster_slave,license_slave \
		--env INIT_GENERAL_PASS_4_SYMM_KEY=general-changeme \
		--env INIT_LICENSE_MASTER=https://license-master:8089 \
		--env INIT_CLUSTERING_PASS_4_SYMM_KEY=clustering-changeme \
		--env INIT_CLUSTERING_CLUSTER_MASTER=https://cluster-master:8089 \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2

deploy-dmc:
	docker service create \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 512m \
		--name dmc \
		--container-label splunk.cluster=dmc \
		--label splunk.cluster=dmc \
		--network splunk \
		--env SPLUNK_START_ARGS=--accept-license \
		--env SPLUNK_ROLES=license_slave,cluster_searchhead,dmc \
		--env INIT_CLUSTERING_PASS_4_SYMM_KEY=clustering-changeme \
		--env INIT_CLUSTERING_CLUSTER_MASTER=https://cluster-master:8089 \
		--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
		--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
		--env INIT_GENERAL_PASS_4_SYMM_KEY=general-changeme \
		--env INIT_LICENSE_MASTER=https://license-master:8089 \
		--env INIT_KVSTORE_ENABLED=false \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth0 \
		$$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2

deploy-deployment-server:
	docker service create \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 256m \
		--name deployment-server \
		--container-label splunk.cluster=deployment-server \
		--label splunk.cluster=deployment-server \
		--network splunk \
		--env SPLUNK_START_ARGS=--accept-license \
		--env SPLUNK_ROLES=deployment_server \
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
		$$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2

deploy-data-collector-hec:
	docker service create \
		--mode replicated \
		--replicas 2 \
		--reserve-memory 256m \
		--name data-collector-hec \
		--container-label splunk.cluster=data-collector-hec \
		--label splunk.cluster=data-collector-hec \
		--network splunk \
		--env SPLUNK_START_ARGS=--accept-license \
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
		$$(docker-machine ip registry)/outcoldman/splunk-cluster:6.4.2

deploy: deploy-consul deploy-license-master deploy-cluster-master deploy-shc-deployer deploy-shc-member deploy-cluster-slave deploy-dmc deploy-data-collector-hec deploy-data-collector-internal deploy-lb deploy-deployment-server

clean:
	docker service rm consul consul-first license-master cluster-master shc-deployer shc-member cluster-slave dmc data-collector-hec data-collector-internal lb deployment-server

