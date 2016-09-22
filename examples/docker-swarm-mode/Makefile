export SPLUNK_CLUSTER_VERSION ?= 6.4.3
export SPLUNK_CLUSTER_DOCKER_IMAGE_PATH ?= ${USER}
# If you don't want (cannot) delete old volumes, just use SALT to use new one
SALT ?=

setup-clean:
	seq 0 5 | xargs -I @ docker-machine rm -f splunk@

setup:
	seq 0 5 | xargs -P 6 -I @ bash -c "docker-machine create \
		--driver=virtualbox \
		--virtualbox-disk-size=200000 \
		--virtualbox-memory=1536 \
		--virtualbox-cpu-count=2 \
		splunk@"
	seq 0 5 | xargs -P 6 -I @ docker-machine regenerate-certs --force splunk@
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
	cd ./../../splunk-cluster && docker build -t $(SPLUNK_CLUSTER_DOCKER_IMAGE_PATH)/splunk-cluster:$(SPLUNK_CLUSTER_VERSION) -t $(SPLUNK_CLUSTER_DOCKER_IMAGE_PATH)/splunk-cluster:latest .

push:
	docker push $(SPLUNK_CLUSTER_DOCKER_IMAGE_PATH)/splunk-cluster:$(SPLUNK_CLUSTER_VERSION)
	docker push $(SPLUNK_CLUSTER_DOCKER_IMAGE_PATH)/splunk-cluster:latest

download-image:
	seq 0 5 | xargs -P 6 -I @ bash -c 'eval $$(docker-machine env splunk@); docker pull $(SPLUNK_CLUSTER_DOCKER_IMAGE_PATH)/splunk-cluster:$(SPLUNK_CLUSTER_VERSION)'

download-image-using-swarm:
	docker service create \
		--mode global \
		--name download-image \
		--with-registry-auth \
		$(SPLUNK_CLUSTER_DOCKER_IMAGE_PATH)/splunk-cluster:$(SPLUNK_CLUSTER_VERSION) entrypoint.sh sleep infinity
	sleep 5
	while docker service ps download-image | grep Preparing 1>/dev/null 2>&1; do sleep 1; done
	docker service rm download-image

deploy-cluster-master:
	ls *.lic 1> /dev/null 2>&1;
	docker service create \
		--constraint "node.id == $$(docker node ls | grep '*' | awk '{print($$1)}')" \
		--mode replicated \
		--replicas 1 \
		--name cluster-master \
		--container-label splunk.cluster=cluster-master \
		--label splunk.cluster=cluster-master \
		--network splunk \
		--mount "type=volume,source=cluster-master-etc$(SALT),destination=/opt/splunk/etc" \
		--mount "type=volume,source=cluster-master-var$(SALT),destination=/opt/splunk/var" \
		--with-registry-auth \
		--publish 9000:8000 \
		--env "SPLUNK_START_ARGS=--accept-license --answer-yes --no-prompt" \
		--env "SPLUNK_BEFORE_START_CMD_1=version \$$SPLUNK_START_ARGS" \
		--env "SPLUNK_BEFORE_START_CMD_2=cmd python /opt/splunk/bin/splunk_setup.py --configure" \
		--env "SPLUNK_BEFORE_START_CMD_3=cmd python /opt/splunk/bin/splunk_setup.py --add-licenses /opt/" \
		--env "SPLUNK_ADD_1=role service_discovery_role -auth admin:changeme" \
		--env "SPLUNK_ADD_2=user service_discovery_user -password service_discovery_password -role service_discovery_role -auth admin:changeme" \
		--env "SPLUNK_CMD_1=cmd python /opt/splunk/bin/splunk_setup.py --wait-splunk 'https://shc-member-01:8089' '(shc_member|shc_captain)'" \
		--env "SPLUNK_CMD_2=cmd python /opt/splunk/bin/splunk_setup.py --wait-splunk 'https://shc-member-02:8089' '(shc_member|shc_captain)'" \
		--env "SPLUNK_CMD_3=cmd python /opt/splunk/bin/splunk_setup.py --wait-splunk 'https://shc-member-03:8089' '(shc_member|shc_captain)'" \
		--env "SPLUNK_CMD_4=add search-server shc-member-01:8089 -remoteUsername admin -remotePassword changed -auth admin:changeme" \
		--env "SPLUNK_CMD_5=add search-server shc-member-02:8089 -remoteUsername admin -remotePassword changed -auth admin:changeme" \
		--env "SPLUNK_CMD_6=add search-server shc-member-03:8089 -remoteUsername admin -remotePassword changed -auth admin:changeme" \
		--env "SPLUNK_CMD_7=status" \
		--env "CONF__inputs__default__host=cluster-master" \
		--env "CONF__inputs__http__useDeploymentServer=true" \
		--env "CONF__outputs__indexAndForward__index=false" \
		--env "CONF__outputs__indexer_discovery:search_head_peers__master_uri=https://cluster-master:8089" \
		--env "CONF__outputs__indexer_discovery:search_head_peers__pass4SymmKey=indexdiscovery-changeme" \
		--env "CONF__outputs__tcpout:splunk_search_head_peers_group__autoLB=true" \
		--env "CONF__outputs__tcpout:splunk_search_head_peers_group__indexerDiscovery=search_head_peers" \
		--env "CONF__outputs__tcpout__defaultGroup=splunk_search_head_peers_group" \
		--env "CONF__outputs__tcpout__forwardedindex.filter.disable =true" \
		--env "CONF__outputs__tcpout__indexAndForward=false" \
		--env "CONF__restmap__broker:broker__requireAuthentication=true" \
		--env "CONF__collections__service_discovery__disabled=false" \
		--env "CONF__meta__collections/service_discovery__access=read : [ service_discovery_role ], write : [ service_discovery_role ]" \
		--env "CONF__server__clustering__cluster_label=cluster" \
		--env "CONF__server__clustering__mode=master" \
		--env "CONF__server__clustering__pass4SymmKey=clustering-changeme" \
		--env "CONF__server__clustering__replication_factor=3" \
		--env "CONF__server__clustering__search_factor=2" \
		--env "CONF__server__general__serverName=cluster-master" \
		--env "CONF__server__general__pass4SymmKey=general-changeme" \
		--env "CONF__server__deployment__pass4SymmKey=deployment-changeme" \
		--env "CONF__server__indexer_discovery__pass4SymmKey=indexdiscovery-changeme" \
		--env "CONF__server__shclustering__id=776D2949-B2DA-405E-96B3-B6688C87AB7D" \
		--env "CONF__server__shclustering__pass4SymmKey=shclustering-changeme" \
		--env "CONF__server__shclustering__shcluster_label=shcluster" \
		--env "CONF__serverclass__global__crossServerChecksum=true" \
		--env "CONF__serverclass__serverClass:data-collector-hec:app:splunk_httpinput__restartSplunkd=true" \
		--env "CONF__serverclass__serverClass:data-collector-hec__whitelist.0=data-collector-hec" \
		--env "CONF__web__settings__login_content=Cluster Master" \
		--env "CONF__etc/master-apps/cluster-deployment__indexes__main__repFactor=auto" \
		--env "CONF__etc/master-apps/cluster-deployment__indexes__history__repFactor=auto" \
		--env "CONF__etc/master-apps/cluster-deployment__indexes__summary__repFactor=auto" \
		--env "CONF__etc/master-apps/cluster-deployment__indexes__splunklogger__repFactor=auto" \
		--env "CONF__etc/master-apps/cluster-deployment__indexes___internal__repFactor=auto" \
		--env "CONF__etc/master-apps/cluster-deployment__indexes___audit__repFactor=auto" \
		--env "CONF__etc/master-apps/cluster-deployment__indexes___thefishbucket__repFactor=auto" \
		--env "CONF__etc/deployment-apps/splunk_httpinput__inputs__http__dedicatedIoThreads=2" \
		--env "CONF__etc/deployment-apps/splunk_httpinput__inputs__http__maxThreads=0" \
		--env "CONF__etc/deployment-apps/splunk_httpinput__inputs__http__allowSslRenegotiation=true" \
		--env "CONF__etc/deployment-apps/splunk_httpinput__inputs__http__disabled=false" \
		--env "CONF__etc/deployment-apps/splunk_httpinput__inputs__http__useDeploymentServer=false" \
		--env "CONF__etc/deployment-apps/splunk_httpinput__inputs__http__port=8088" \
		--env "CONF__etc/deployment-apps/splunk_httpinput__inputs__http__allowSslCompression=true" \
		--env "CONF__etc/deployment-apps/splunk_httpinput__inputs__http__sslVersions=*,-ssl2" \
		--env "CONF__etc/deployment-apps/splunk_httpinput__inputs__http__enableSSL=true" \
		--env "CONF__etc/deployment-apps/splunk_httpinput__inputs__http__maxSockets=0" \
		--env "CONF__etc/deployment-apps/splunk_httpinput__inputs__http://default__token=EF211A51-D6AC-4045-8CD6-F730939AC518" \
		--env "CONF__etc/deployment-apps/splunk_httpinput__inputs__http://default__disabled=False" \
		$(SPLUNK_CLUSTER_DOCKER_IMAGE_PATH)/splunk-cluster:$(SPLUNK_CLUSTER_VERSION)
	while [[ "$$(docker ps -qa --filter=label=com.docker.swarm.service.name=cluster-master)" == "" ]]; do sleep 1; done
	ls *.lic | xargs -I @ docker cp @ $$(docker ps -qa --filter=label=com.docker.swarm.service.name=cluster-master):/opt/

deploy-shc-member:
	for number in $(shell seq 3); do \
		docker service create \
			--constraint "node.labels.index == $${number}" \
			--name shc-member-0$${number} \
			--mode replicated \
			--replicas 1 \
			--container-label splunk.cluster=shc-member \
			--label splunk.cluster=shc-member \
			--network splunk \
			--mount "type=volume,source=shc-member-0$${number}-etc$(SALT),destination=/opt/splunk/etc" \
			--mount "type=volume,source=shc-member-0$${number}-var$(SALT),destination=/opt/splunk/var" \
			--with-registry-auth \
			--publish 800$${number}:8000 \
			--env "SPLUNK_START_ARGS=--accept-license --answer-yes --no-prompt" \
			--env "SPLUNK_BEFORE_START_CMD_1=version \$$SPLUNK_START_ARGS" \
			--env "SPLUNK_BEFORE_START_CMD_2=cmd python /opt/splunk/bin/splunk_setup.py --wait-splunk 'https://cluster-master:8089' cluster_master kv_store license_master" \
			--env "SPLUNK_BEFORE_START_CMD_3=cmd python /opt/splunk/bin/splunk_setup.py --configure" \
			--env "SPLUNK_BEFORE_START_CMD_4=edit user admin -password changed -role admin -auth admin:changeme" \
			--env "SPLUNK_BEFORE_START_CMD_5=cmd python -c 'open(\"/opt/splunk/etc/.ui_login\", \"a\").close()'" \
			--env "SPLUNK_CMD_1=cmd python /opt/splunk/bin/splunk_setup.py --shc-autobootstrap 3 'https://shc-member-0$${number}:8089' admin changed 'https://cluster-master:8089/servicesNS/nobody/system/storage/collections/data/service_discovery' service_discovery_user service_discovery_password" \
			--env "SPLUNK_CMD_2=status" \
			--env "CONF__etc/apps/splunk_management_console__app__install__state=disabled" \
			--env "CONF__outputs__indexAndForward__index=false" \
			--env "CONF__outputs__indexer_discovery:search_head_peers__master_uri=https://cluster-master:8089" \
			--env "CONF__outputs__indexer_discovery:search_head_peers__pass4SymmKey=indexdiscovery-changeme" \
			--env "CONF__outputs__tcpout:splunk_search_head_peers_group__autoLB=true" \
			--env "CONF__outputs__tcpout:splunk_search_head_peers_group__indexerDiscovery=search_head_peers" \
			--env "CONF__outputs__tcpout__defaultGroup=splunk_search_head_peers_group" \
			--env "CONF__outputs__tcpout__forwardedindex.filter.disable =true" \
			--env "CONF__outputs__tcpout__indexAndForward=false" \
			--env "CONF__server__general__pass4SymmKey=general-changeme" \
			--env "CONF__server__general__serverName=shc-member-0$${number}" \
			--env "CONF__server__license__master_uri=https://cluster-master:8089" \
			--env "CONF__server__clustering__cluster_label=cluster" \
			--env "CONF__server__clustering__master_uri=https://cluster-master:8089" \
			--env "CONF__server__clustering__mode=searchhead" \
			--env "CONF__server__clustering__pass4SymmKey=clustering-changeme" \
			--env "CONF__server__replication_port://9889__disabled=false" \
			--env "CONF__server__shclustering__id=776D2949-B2DA-405E-96B3-B6688C87AB7D" \
			--env "CONF__server__shclustering__conf_deploy_fetch_url=https://cluster-master:8089" \
			--env "CONF__server__shclustering__disabled=false" \
			--env "CONF__server__shclustering__election_timeout_ms=10000" \
			--env "CONF__server__shclustering__mgmt_uri=https://shc-member-0$${number}:8089" \
			--env "CONF__server__shclustering__pass4SymmKey=shclustering-changeme" \
			--env "CONF__server__shclustering__replication_factor=3" \
			--env "CONF__server__shclustering__shcluster_label=shcluster" \
			--env "CONF__web__settings__login_content=SHC Member" \
			--env "CONF__inputs__default__host=shc-member-0$${number}" \
			$(SPLUNK_CLUSTER_DOCKER_IMAGE_PATH)/splunk-cluster:$(SPLUNK_CLUSTER_VERSION); \
	done

deploy-cluster-slave:
	for number in $(shell seq 3); do \
		docker service create \
			--constraint "node.labels.index == $${number}" \
			--name cluster-slave-0$${number} \
			--mode replicated \
			--replicas 1 \
			--container-label splunk.cluster=cluster-slave \
			--label splunk.cluster=cluster-slave \
			--network splunk \
			--mount "type=volume,source=cluster-slave-etc$(SALT),destination=/opt/splunk/etc" \
			--mount "type=volume,source=cluster-slave-var$(SALT),destination=/opt/splunk/var" \
			--with-registry-auth \
			--publish 808$${number}:8088 \
			--env "SPLUNK_START_ARGS=--accept-license --answer-yes --no-prompt" \
			--env "SPLUNK_BEFORE_START_CMD_1=version \$$SPLUNK_START_ARGS" \
			--env "SPLUNK_BEFORE_START_CMD_2=cmd python /opt/splunk/bin/splunk_setup.py --wait-splunk 'https://cluster-master:8089' cluster_master license_master" \
			--env "SPLUNK_BEFORE_START_CMD_3=cmd python /opt/splunk/bin/splunk_setup.py --configure" \
			--env "SPLUNK_CMD_1=status" \
			--env "CONF__etc/apps/splunk_management_console__app__install__state=disabled" \
			--env "CONF__server__general__serverName=cluster-slave-0$${number}" \
			--env "CONF__server__general__pass4SymmKey=general-changeme" \
			--env "CONF__server__license__master_uri=https://cluster-master:8089" \
			--env "CONF__server__kvstore__disabled=true" \
			--env "CONF__web__settings__startwebserver=false" \
			--env "CONF__server__clustering__cluster_label=cluster" \
			--env "CONF__server__clustering__mode=slave" \
			--env "CONF__server__clustering__pass4SymmKey=clustering-changeme" \
			--env "CONF__server__clustering__master_uri=https://cluster-master:8089" \
			--env "CONF__server__replication_port://9888__disabled=false" \
			--env "CONF__server__clustering__register_register_replication_address=cluster-slave-0$${number}" \
			--env "CONF__server__clustering__register_replication_address=cluster-slave-0$${number}" \
			--env "CONF__server__clustering__register_search_address=cluster-slave-0$${number}" \
			--env "CONF__inputs__splunktcp://9997__disabled=false" \
			--env "CONF__inputs__default__host=cluster-slave-0$${number}" \
			--env "CONF__server__deployment__pass4SymmKey=deployment-changeme" \
			--env "CONF__deploymentclient__deployment-client__disabled=false" \
			--env "CONF__deploymentclient__deployment-client__clientName=data-collector-hec" \
			--env "CONF__deploymentclient__target-broker:deploymentServer__targetUri=cluster-master:8089" \
			$(SPLUNK_CLUSTER_DOCKER_IMAGE_PATH)/splunk-cluster:$(SPLUNK_CLUSTER_VERSION); \
	done

deploy-cluster-slave-2-more:
	for number in $(shell seq 4 5); do \
		docker service create \
			--constraint "node.labels.index == $${number}" \
			--name cluster-slave-0$${number} \
			--mode replicated \
			--replicas 1 \
			--container-label splunk.cluster=cluster-slave \
			--label splunk.cluster=cluster-slave \
			--network splunk \
			--mount "type=volume,source=cluster-slave-etc$(SALT),destination=/opt/splunk/etc" \
			--mount "type=volume,source=cluster-slave-var$(SALT),destination=/opt/splunk/var" \
			--with-registry-auth \
			--publish 808$${number}:8088 \
			--env "SPLUNK_START_ARGS=--accept-license --answer-yes --no-prompt" \
			--env "SPLUNK_BEFORE_START_CMD_1=version \$$SPLUNK_START_ARGS" \
			--env "SPLUNK_BEFORE_START_CMD_2=cmd python /opt/splunk/bin/splunk_setup.py --wait-splunk 'https://cluster-master:8089' cluster_master license_master" \
			--env "SPLUNK_BEFORE_START_CMD_3=cmd python /opt/splunk/bin/splunk_setup.py --configure" \
			--env "SPLUNK_CMD_1=status" \
			--env "CONF__etc/apps/splunk_management_console__app__install__state=disabled" \
			--env "CONF__server__general__serverName=cluster-slave-0$${number}" \
			--env "CONF__server__general__pass4SymmKey=general-changeme" \
			--env "CONF__server__license__master_uri=https://cluster-master:8089" \
			--env "CONF__server__kvstore__disabled=true" \
			--env "CONF__web__settings__startwebserver=false" \
			--env "CONF__server__clustering__cluster_label=cluster" \
			--env "CONF__server__clustering__mode=slave" \
			--env "CONF__server__clustering__pass4SymmKey=clustering-changeme" \
			--env "CONF__server__clustering__master_uri=https://cluster-master:8089" \
			--env "CONF__server__replication_port://9888__disabled=false" \
			--env "CONF__server__clustering__register_register_replication_address=cluster-slave-0$${number}" \
			--env "CONF__server__clustering__register_replication_address=cluster-slave-0$${number}" \
			--env "CONF__server__clustering__register_search_address=cluster-slave-0$${number}" \
			--env "CONF__inputs__splunktcp://9997__disabled=false" \
			--env "CONF__inputs__default__host=cluster-slave-0$${number}" \
			--env "CONF__server__deployment__pass4SymmKey=deployment-changeme" \
			--env "CONF__deploymentclient__deployment-client__disabled=false" \
			--env "CONF__deploymentclient__deployment-client__clientName=data-collector-hec" \
			--env "CONF__deploymentclient__target-broker:deploymentServer__targetUri=cluster-master:8089" \
			$(SPLUNK_CLUSTER_DOCKER_IMAGE_PATH)/splunk-cluster:$(SPLUNK_CLUSTER_VERSION); \
	done

deploy: deploy-cluster-master deploy-shc-member deploy-cluster-slave

clean:
	-docker service rm cluster-master
	-seq 3 | xargs -P 3 -I @ docker service rm shc-member-0@
	-seq 3 | xargs -P 3 -I @ docker service rm cluster-slave-0@

clean-images:
	-seq 0 5 | xargs -P 6 -I @ bash -c 'eval $$(docker-machine env splunk@); docker rmi -f $$(docker images -q);'

clean-volumes:
	-seq 0 5 | xargs -P 6 -I @ bash -c 'eval $$(docker-machine env splunk@); docker kill $$(docker ps -q); docker rm -v $$(docker ps -aq); docker volume rm $$(docker volume ls -q)'

clean-all: clean clean-volumes
