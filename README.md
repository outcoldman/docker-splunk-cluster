# Cluster-aware Splunk Enterprise docker image 

## Introduction

> NOTE: I'm working at Splunk, but this is not an official Splunk images.
> I build them in my free time when I'm not at work. I have some knowledge
> about Splunk, but you should think twice before putting them in
> production. I run these images on my own home server just for
> my personal needs. If you have any issues - feel free to open a
> [bug](https://github.com/outcoldman/docker-splunk-cluster/issues).

> Use for learning purposes.

This repository contains set of examples how to run Splunk Enterprise cluster in Docker,
including Search Head Cluster and Indexing Cluster.

## Version

Based on `outcoldman/splunk:6.4.2`.

* Version: `6.4.2`
* Build: `00f5bb3fa822`

## How it works

### Cluster-aware image

These examples depend on the custom image, which you can build using `./node` folder.
This image is based on `outcoldman/splunk` and includes several changes:

- Adds consul binary to the image. We use consul for service discovery.
- Adds Splunk `splunkcluster` index, which will be used to send here all internal
    logs about the cluster from `consul` and `load balancer`.
- Adds deployment python scripts to `/opt/splunk-deployment`, which are executed
    only on first start by using `SPLUNK_CMD` as `cmd python /opt/splunk-deployment/init.py`.
- Register `consul` as scripted input, so it always will be launched with `splunkd`.
    All logs from `consul` go to the `splunkcluster` index.

> NOTE: do not override `SPLUNK_CMD` when you start this image, this will disable
cluster initialization.

#### Configuration

- `SPLUNK_ROLES` define the roles for the container. Use comma to define multiple roles (which are compatible).
    - `license_master`
    - `license_slave`
    - `cluster_master`
    - `cluster_searchhead`
    - `cluster_slave`
    - `shc_deployer`
    - `shc_member`
    - `shc_deployer_client`
    - `hw_forwarder`

- `INIT_KVSTORE_ENABLED` - force to enable KVStore.
- `INIT_WEB_ENABLED` - force to enable Web.
- `INIT_INDEXING_ENABLED` - force to enable Indexing.
- `INIT_WEB_SETTINGS_PREFIX` - set prefix for Web.
- `INIT_INDEX_DISCOVERY_MASTER_URI` - sets uri to Cluster Master with enabled Index Discovery. When indexing is off. Defaults to `https://cluster-master:8089`.
- `INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY` - set index discovery `pass4SymmKey`. When indexing is off. Defaults to `indexdiscovery-changeme`.

##### License Master

- Add licenses to the pool if it will find any `*.lic` files under `/opt/splunk-deployment/`.
- Does not require KVStore.
- Does not require Splunk Web.
- Does not require Indexing.

- `INIT_GENERAL_PASS_4_SYMM_KEY` - set `pass4SymmKey` for the License Cluster. Defaults to `general-changeme`.

##### License Slave

- Does not require KVStore.
- Does not require Splunk Web.
- Does not require Indexing.

- `INIT_GENERAL_PASS_4_SYMM_KEY` - set `pass4SymmKey` for the License Cluster. Defaults to `general-changeme`.
- `INIT_LICENSE_MASTER` - uri to License Master. Defaults to `https://license-master:8089`.


##### Cluster Master

- Does not require KVStore.
- Does not require Splunk Web.
- Does not require Indexing.

- Sets `repFactor = auto` for all default indexes. This configuration will be deployed to indexers using `master-apps` folder.
- Sets up index discovery.
- Sets clustering `mode = master`.

- `INIT_CLUSTERING_PASS_4_SYMM_KEY` - set `pass4SymmKey` for Indexing Cluster. Defaults to `clustering-changeme`.
- `INIT_CLUSTERING_REPLICATION_FACTOR` - set replication factor. Defaults to `1`.
- `INIT_CLUSTERING_SEARCH_FACTOR` - set search factor. Defaults to `1`.
- `INIT_CLUSTERING_CLUSTER_LABEL` - set cluster label. Defaults to `cluster`.
- `INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY` - set index discovery `pass4SymmKey`. Defaults to "indexdiscovery-changeme".

##### Cluster Search Head

- Require KVStore.
- Require Splunk Web.
- Does not require Indexing.

- Sets clustering `mode = searchhead`.

- `INIT_CLUSTERING_PASS_4_SYMM_KEY` - set `pass4SymmKey` for Indexing Cluster. Defaults to `clustering-changeme`.
- `INIT_CLUSTERING_CLUSTER_MASTER` - set cluster master uri. Defaults to `https://cluster-master:8089`.

Before starting Splunk after applying configuration changes waits for the `cluster_master` 
role in cluster master defined with `INIT_CLUSTERING_CLUSTER_MASTER`.

##### Cluster Slave

- Does not require KVStore.
- Does not require Splunk Web.
- Require Indexing.

- Sets clustering `mode = slave`.
- Enables listening on `9997` for forwarded data.

- `INIT_CLUSTERING_PASS_4_SYMM_KEY` - set `pass4SymmKey` for Indexing Cluster. Defaults to `clustering-changeme`.
- `INIT_CLUSTERING_CLUSTER_MASTER` - set cluster master uri. Defaults to `https://cluster-master:8089`.

Before starting Splunk after applying configuration changes waits for the `cluster_master` 
role in cluster master defined with `INIT_CLUSTERING_CLUSTER_MASTER`.

##### SHC Deployer

- Does not require KVStore.
- Does not require Splunk Web.
- Does not require Indexing.

- `INIT_SHCLUSTERING_PASS_4_SYMM_KEY` - set `pass4SymmKey` for Search Head Cluster. Defaults to `shclustering-changeme`.

##### SHC Member

- Require KVStore.
- Require Splunk Web.
- Does not require Indexing.

- `INIT_SHCLUSTERING_PASS_4_SYMM_KEY` - set `pass4SymmKey` for Search Head Cluster. Defaults to `shclustering-changeme`.
- `INIT_SHCLUSTERING_MGMT_URI` - set management uri of current server. Defaults to `https://$HOSTNAME:8089`.
- `INIT_SHCLUSTERING_REPLICATION_FACTOR` - set replication factor. Defaults to `3`.
- `INIT_SHCLUSTERING_SHCLUSTER_LABEL` - set Search Head Cluster label. Defaults to `shcluster`.
- `INIT_SHCLUSTER_AUTOBOOTSTRAP` - auto bootstrap Search Head Cluster on this number of members. Defaults to `3`.

After start this role also is trying to auto bootstrap Search Head Cluster or add itself
to existing Search Head Cluster. Using consul every SHC Member elects itself as a Consul Leader on the Consul Service
(not related to Search Head Cluster Captain), adds itself to the list of SHC Members. Checks the current list, if 
number of members is less than `INIT_SHCLUSTER_AUTOBOOTSTRAP` - just release leadership on Consul Service. If equal to -
does bootstrapping of SHC, if larger - adds itself to Search Head Cluster.

##### SHC Deployer Client

- Does not require KVStore.
- Does not require Splunk Web.
- Does not require Indexing.

- `INIT_SHCLUSTERING_SHCDEPLOYER` - set uri to Search Head Cluster deployer. Defaults to `https://shc-deployer:8089`.

Before starting Splunk after applying configuration changes waits for the
Search Head Cluster Deployer defined with `INIT_SHCLUSTERING_SHCDEPLOYER`.

##### HW Forwarder

- Does not require KVStore.
- Does not require Splunk Web.
- Does not require Indexing.

- `INIT_ADD_UDP_PORT` - add listening on port defined with this variable, sets `connection_host = dns`,
    `index = splunkcluster` and register this as a service in consul with name `syslog`.

#### Files listing in image

##### /

- `consul.sh` - script for scripted input, rule how we launch `consul`. Important, that
    we persist consul data in `"$SPLUNK_HOME/var/consul"`.
- `consul_check.sh` - check script used by consul to verify that `splunkd` is alive.
- `indexes.conf` - define `splunkcluster` index, which will be used to send logs from
    `consul` and `load balancer`.
- `inputs.conf` - definition of scripted input, which will allow us to launch `consul`
    with `splunkd`.

##### /deployment

- `init.py` - startup script, which will be used to initialize the cluster. Invoked with
    cmd python /opt/splunk-deployment/init.py`.
- `init_consul.py` - helper functions to work with local consul.
- `init_helpers.py` - helper functions.
- `init_<role>.py` - rules how to initialize the role.
- `_disable_<what>/` - set of default configuration files which allow to disable
    this feature. For example `_disable_indexing` contains configuration files to
    forward events to the indexing cluster using index discovery.
- `<ROLE>` - set of configurations rules which will be applied to defined role.

### Load balancing image

Folder `lb` is building HTTP load balancing image. It is based on `consul`, `consul-template`
and `haproxy`. `consul-template` listen for services updates in the consul and
regenerates the `haproxy` configuration.

Ports:

- `8000` - load balances between SHC servers, using cookie `SERVERID`.
- `8100` - redirects to Cluster Master.
- `8200` - redirects to DMC.
- `8300` - redirects to License Master.
- `8500` - redirects to consul.

> NOTE: consul is not secured by default.

## Use it

### Deploy

#### On docker instance

```
docker-compose build
docker-compose up -d
docker-compose scale cluster-slave=4 shc-member=3
```

Watch for status of deployment:
- Open `http://<docker>:8500` to watch for all green services and hosts.
- Watch for `docker-compose logs -f shc-member` for the line `Successfully bootstrapped this node as the captain with the given servers.`.
    This will mean that SHC is bootstrapped.
- Open Cluster Master web on `http://<docker>:8100` and check `Indexer Clustering: Master Node` page
    that Indexes are replicated and ready for search.
- Open SHC on `http://<docker>:8000` and check that you see logs from all instances `index="_internal" | stats count by host`.

You can scale up later with

```
docker-compose scale cluster-slave=8 shc-member=5
```

#### On docker swarm

> TODO...

### Examples after setup

#### Install application on SHC using SHC Deployer

```
docker cp ~/Downloads/splunk_app_aws shc-deployer:/opt/splunk/etc/shcluster/apps/
docker exec shc-deployer entrypoint.sh chown -R splunk:splunk /opt/splunk/etc/shcluster/apps/
docker exec shc-deployer entrypoint.sh splunk apply shcluster-bundle -restart true --answer-yes -target https://$(docker ps --filter=label=splunk.cluster=shc-member -q | head -1):8089 -auth admin:changeme
```

## TODO:

- [ ] Secret storage for getting secrets (currently everything is in plain text from env variables). Might use Vault from HashiCorp.
- [ ] DMC Server (with all configurations setup automatically)
- [ ] Deployment Server
- [ ] Forwarders
- [ ] Encrypt consul communication
- [ ] CA Authority. Do not skip certificate verification.
- [ ] Send consul logs to Splunk
- [ ] Check if there are better way to configure SSO (including trustedIP)
- [ ] On SHC we should log IP addresses with "tools.proxy.on = True"
- [ ] Use consul http checks for web and mgmt ports
- [ ] Collecting logs from consul server
- [ ] Upgrade to consul-template 0.16.0 rtm.
- [ ] SHC Members require restart (possible SHC Deployer should do rolling restart after bootstrap)
- [ ] Custom CA.
- [ ] Secure by default `8500`.
- [ ] Load balancer using hostnames instead of services for cluster-master, dmc and consul.
- [ ] Expect `.lic` files in better place.
- [ ] Use `socket` to get fqdn.
- [ ] SHC Autobootstrap should support removed members.
- [ ] Make all consul requests with retry.
