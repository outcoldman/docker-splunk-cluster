swarm-setup-clean:
	docker-machine rm -f registry splunk1 splunk2 splunk3

swarm-setup:
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
	eval $$(docker-machine env splunk1) && docker swarm init --listen-addr $$(docker-machine ip splunk1) --secret splunk_swarm_cluster && docker network create --driver=overlay splunk
	@echo "Do (with --ca-hash from above): "
	@echo "eval $$(docker-machine env splunk2) && docker swarm join --listen-addr $$(docker-machine ip splunk2) --secret splunk_swarm_cluster --ca-hash HASH_HERE $$(docker-machine ip splunk1):2377" 
	@echo "eval $$(docker-machine env splunk3) && docker swarm join --listen-addr $$(docker-machine ip splunk3) --secret splunk_swarm_cluster --ca-hash HASH_HERE $$(docker-machine ip splunk1):2377"

swarm-build:
	cd ./node && docker build -t $$(docker-machine ip registry)/node . && docker push $$(docker-machine ip registry)/node
	cd ./lb && docker build -t $$(docker-machine ip registry)/lb . && docker push $$(docker-machine ip registry)/lb
	cd ./consul && docker build -t $$(docker-machine ip registry)/consul . && docker push $$(docker-machine ip registry)/consul

swarm-up-consul:
	docker service create \
		--mode replicated \
		--replicas 3 \
		--reserve-memory 128m \
		--name consul \
		--mode replicated \
		--label splunk.cluster=consul \
		--network splunk \
		--env CONSUL_DATA_DIR="/consul/data" \
		--env CONSUL_DC="dc" \
		--env CONSUL_DOMAIN="splunk" \
		--env CONSUL_CLIENT="0.0.0.0" \
		--env CONSUL_BOOTSTRAP_EXPECT="3" \
		--env CONSUL_JOIN="consul" \
		--env CONSUL_ADVERTISE_INTERFACE=eth2 \
		--publish 8500:8500 \
		$$(docker-machine ip registry)/consul

swarm-up-license-master:
	docker service create \
		--constraint "node.role == manager" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 512m \
		--name license-master \
		--label splunk.cluster=license-master \
		--network splunk \
		--env SPLUNK_START_ARGS=--accept-license \
		--env SPLUNK_ROLES=license_master \
		--env INIT_GENERAL_PASS_4_SYMM_KEY=general-changeme \
		--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
		--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
		--env INIT_WEB_ENABLED=true \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth2 \
		$$(docker-machine ip registry)/node

swarm-up-cluster-master:
	docker service create \
		--constraint "node.role == manager" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 512m \
		--name cluster-master \
		--label splunk.cluster=cluster-master \
		--network splunk \
		--env SPLUNK_START_ARGS=--accept-license \
		--env SPLUNK_ROLES=cluster_master,license_slave \
		--env INIT_CLUSTERING_PASS_4_SYMM_KEY=clustering-changeme \
		--env INIT_CLUSTERING_REPLICATION_FACTOR=1 \
		--env INIT_CLUSTERING_SEARCH_FACTOR=1 \
		--env INIT_CLUSTERING_CLUSTER_LABEL=cluster1 \
		--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
		--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
		--env INIT_GENERAL_PASS_4_SYMM_KEY=general-changeme \
		--env INIT_LICENSE_MASTER=https://license-master:8089 \
		--env INIT_WEB_ENABLED=true \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		--env CONSUL_ADVERTISE_INTERFACE=eth2 \
		$$(docker-machine ip registry)/node

swarm-up-shc-deployer:
	docker service create \
		--constraint "node.role == manager" \
		--mode replicated \
		--replicas 1 \
		--reserve-memory 512m \
		--name shc-deployer \
		--label splunk.cluster=shc-deployer \
		--env SPLUNK_START_ARGS=--accept-license \
		--env SPLUNK_ROLES=shc-deployer \
		--env INIT_SHCLUSTERING_PASS_4_SYMM_KEY=shclustering-changeme \
		--env INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY=indexdiscovery-changeme \
		--env INIT_INDEX_DISCOVERY_MASTER_URI=https://cluster-master:8089 \
		--env CONSUL_HOST=consul \
		--env CONSUL_DC=dc \
		--env CONSUL_DOMAIN=splunk \
		$$(docker-machine ip registry)/node

swarm-up: swarm-up-consul swarm-up-license-master swarm-up-cluster-master swarm-up-shc-deployer
	docker service create \
		--constraint "node.role == manager" \
		--env SPLUNK_START_ARGS=--accept-license \
		--env SPLUNK_CMD="cmd python /opt/splunk-deployment/init.py" \
		--env INIT_CLUSTER_REPLICATION_FACTOR=1 \
		--env INIT_CLUSTER_SEARCH_FACTOR=1 \
		--publish 9000:8000 \
		--replicas 1 \
		--mode replicated \
		--reserve-memory 1024m \
		--name cluster-master \
		--network splunk \
		$$(docker-machine ip registry)/cluster-master
	docker service create \
		--env SPLUNK_START_ARGS=--accept-license \
		--env SPLUNK_CMD="cmd python /opt/splunk-deployment/init.py" \
		--replicas 4 \
		--mode replicated \
		--reserve-memory 512m \
		--name cluster-member \
		--network splunk \
		$$(docker-machine ip registry)/cluster-member
	docker service create \
		--env SPLUNK_START_ARGS=--accept-license \
		--env SPLUNK_CMD="cmd python /opt/splunk-deployment/init.py" \
		--env INIT_SHC_REPLICATION_FACTOR=3 \
		--publish 8000:8000 \
		--replicas 3 \
		--mode replicated \
		--reserve-memory 512m \
		--name shc-member \
		--network splunk \
		$$(docker-machine ip registry)/shc-master

local-clean:
	docker-compose kill
	docker-compose rm -v -f

local-up:
	docker-compose up -d
	docker-compose scale cluster-slave=4 shc-member=3
	@echo "Use 'docker-compose logs -f cluster-master' to wait for Initialized cluster-master as Cluster Master"
