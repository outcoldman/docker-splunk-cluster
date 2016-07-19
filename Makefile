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
		--virtualbox-memory=3072 \
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
	@echo "eval \$(docker-machine env splunk2) && docker swarm join --listen-addr $$(docker-machine ip splunk2) --secret splunk_swarm_cluster --ca-hash HASH_HERE $$(docker-machine ip splunk1):2377" 
	@echo "eval \$(docker-machine env splunk3) && docker swarm join --listen-addr $$(docker-machine ip splunk3) --secret splunk_swarm_cluster --ca-hash HASH_HERE $$(docker-machine ip splunk1):2377"

clean:
	docker-compose kill
	docker-compose rm -v -f

build:
	cd ./cluster-master && docker build -t $$(docker-machine ip registry)/cluster-master . && docker push $$(docker-machine ip registry)/cluster-master
	cd ./cluster-member && docker build -t $$(docker-machine ip registry)/cluster-member . && docker push $$(docker-machine ip registry)/cluster-member
	cd ./shc-member && docker build -t $$(docker-machine ip registry)/shc-master . && docker push $$(docker-machine ip registry)/shc-master

swarm-up:
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

local-up:
	docker-compose up -d
	docker-compose scale cluster-member=4
	docker-compose scale shc-member=3
	@echo "Use 'docker-compose logs -f cluster-master' to wait for Initialized cluster-master as Cluster Master"

bootstrap:
	docker exec -it cluster_shc-member_1 \
		entrypoint.sh \
			splunk \
			bootstrap \
			shcluster-captain \
			-auth admin:changeme \
			-servers_list $$(docker ps --filter=label=splunk.cluster=shc-member -q | xargs -I @ printf "https://@:8089,")
