# Table of Contents

- [Introduction](#introduction)
    - [Version](#version)
- [How it works](#how-it-works)
    - [Cluster-aware image](#cluster-aware-image)
        - [Configuration](#configuration)
            - [License Master](#license-master)
            - [License Slave](#license-slave)
            - [Cluster Master](#cluster-master)
            - [Cluster Search Head](#cluster-search-head)
            - [Cluster Slave](#cluster-slave)
            - [SHC Deployer](#shc-deployer)
            - [SHC Member](#shc-member)
            - [SHC Deployer Client](#shc-deployer-client)
            - [HW Forwarder](#hw-forwarder)
            - [DMC](#dmc)
        - [Files listing in image](#files-listing-in-image)
            - `/`
            - `/deployment`
    - [Load balancing image](#load-balancing-image)
    - [Consul image](#consul-image)
- [Use it](#use-it)
    - [Deploy](#deploy)
        - [On docker instance](#on-docker-instance)
            - [If you do not have a License](#if-you-do-not-have-a-license)
            - [If you have a Splunk Enterprise License](#if-you-have-a-splunk-enterprise-license)
        - [On docker swarm](#on-docker-swarm)
        - [On kubernetes](#on-kubernetes)
    - [Examples after setup](#examples-after-setup)
        - [Install application on SHC using SHC Deployer](#install-application-on-shc-using-shc-deployer)
- [TODO](#todo)


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

The main purpose of this repository is to show how to automate Splunk Cluster deployment.
Below you can find examples how to setup Cluster on Docker, Swarm Mode, Kubernetes (TODO).

### Version

Based on

* Version: `6.4.3`
* Build: `b03109c2bad4`

## How it works

### Cluster-aware image

These examples depend on the custom images, which you can build using `./images/` folder.
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
    - `data_collector`
    - `deployment_server`
    - `deployment_client`

- `INIT_KVSTORE_ENABLED` - force to enable/disable KVStore.
- `INIT_WEB_ENABLED` - force to enable/disable Web.
- `INIT_INDEXING_ENABLED` - force to enable/disable Indexing.
- `INIT_DMC` - force to enable/disable DMC app.
- `INIT_WEB_SETTINGS_PREFIX` - set prefix for Web.
- `INIT_INDEX_DISCOVERY_MASTER_URI` - sets uri to Cluster Master with enabled Index Discovery. When indexing is off. Defaults to `https://cluster-master:8089`.
- `INIT_INDEX_DISCOVERY_PASS_4_SYMM_KEY` - set index discovery `pass4SymmKey`. When indexing is off. Defaults to `indexdiscovery-changeme`.
- `INIT_SERVER_GENERAL_SERVERNAME` - change server name under general
- `INIT_INPUTS_DEFAULT_HOST` - change inputs default host

Consul related variables

- `CONSUL_HOST` - which consul host to join. Defaults to `consul`.
- `CONSUL_ADVERTISE_INTERFACE` - which interface IP to use for advertising.
- `CONSUL_DC` - name of data center. Defaults to `dc`.
- `CONSUL_DOMAIN` - consul default domain. Defaults to `splunk`.

##### License Master

- Add licenses to the pool if it will find any `*.lic` files under `/opt/splunk-deployment/`.
- Does not require KVStore.
- Does not require Splunk Web.
- Does not require Indexing.
- Does not require DMC app.

- `INIT_GENERAL_PASS_4_SYMM_KEY` - set `pass4SymmKey` for the License Cluster. Defaults to `general-changeme`.
- `INIT_WAIT_LICENSE` - wait for license files under `/opt/splunk-deployment/licenses`. Defaults to `False`.

##### License Slave

- Does not require KVStore.
- Does not require Splunk Web.
- Does not require Indexing.
- Does not require DMC app.

- `INIT_GENERAL_PASS_4_SYMM_KEY` - set `pass4SymmKey` for the License Cluster. Defaults to `general-changeme`.
- `INIT_LICENSE_MASTER` - uri to License Master. Defaults to `https://license-master:8089`.


##### Cluster Master

- Does not require KVStore.
- Does not require Splunk Web.
- Does not require Indexing.
- Does not require DMC app.

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
- Does not require DMC app.

- Sets clustering `mode = searchhead`.

- `INIT_CLUSTERING_PASS_4_SYMM_KEY` - set `pass4SymmKey` for Indexing Cluster. Defaults to `clustering-changeme`.
- `INIT_CLUSTERING_CLUSTER_MASTER` - set cluster master uri. Defaults to `https://cluster-master:8089`.

Before starting Splunk after applying configuration changes waits for the `cluster_master` 
role in cluster master defined with `INIT_CLUSTERING_CLUSTER_MASTER`.

##### Cluster Slave

- Does not require KVStore.
- Does not require Splunk Web.
- Require Indexing.
- Does not require DMC app.

- Sets clustering `mode = slave`.
- Enables listening on `9997` for forwarded data.

- `INIT_CLUSTERING_PASS_4_SYMM_KEY` - set `pass4SymmKey` for Indexing Cluster. Defaults to `clustering-changeme`.
- `INIT_CLUSTERING_CLUSTER_MASTER` - set cluster master uri. Defaults to `https://cluster-master:8089`.
- `INIT_CLUSTERING_REGISTER_REPLICATION_ADDRESS` - set replication address, defaults to `socket.getfqdn()`.
- `INIT_CLUSTERING_REGISTER_FORWARDER_ADDRESS`  - set forwarder address, defaults to `socket.getfqdn()`.
- `INIT_CLUSTERING_REGISTER_SEARCH_ADDRESS`  - set search address, defaults to `socket.getfqdn()`.

##### SHC Deployer

- Does not require KVStore.
- Does not require Splunk Web.
- Does not require Indexing.
- Does not require DMC app.

- `INIT_SHCLUSTERING_PASS_4_SYMM_KEY` - set `pass4SymmKey` for Search Head Cluster. Defaults to `shclustering-changeme`.
- `INIT_SHCLUSTERING_SHCLUSTER_LABEL` - set shcluster label. Defaults to `shcluster`.

##### SHC Member

- Require KVStore.
- Require Splunk Web.
- Does not require Indexing.
- Does not require DMC app.

- `INIT_SHCLUSTERING_PASS_4_SYMM_KEY` - set `pass4SymmKey` for Search Head Cluster. Defaults to `shclustering-changeme`.
- `INIT_SHCLUSTERING_MGMT_URI` - set management uri of current server. Defaults to `https://$HOSTNAME:8089`.
- `INIT_SHCLUSTERING_REPLICATION_FACTOR` - set replication factor. Defaults to `3`.
- `INIT_SHCLUSTERING_SHCLUSTER_LABEL` - set Search Head Cluster label. Defaults to `shcluster`.
- `INIT_SHCLUSTER_AUTOBOOTSTRAP` - auto bootstrap Search Head Cluster on this number of members. Defaults to `3`.
- `INIT_SHCLUSTERING_HOSTNAME` - set hostname of current member for SHC membership. Defaults to `socket.getfqdn()`.

After start this role also is trying to auto bootstrap Search Head Cluster or add itself
to existing Search Head Cluster. Using consul every SHC Member elects itself as a Consul Leader on the Consul Service
(not related to Search Head Cluster Captain), adds itself to the list of SHC Members. Checks the current list, if 
number of members is less than `INIT_SHCLUSTER_AUTOBOOTSTRAP` - just release leadership on Consul Service. If equal to -
does bootstrapping of SHC, if larger - adds itself to Search Head Cluster.

##### SHC Deployer Client

- Does not require KVStore.
- Does not require Splunk Web.
- Does not require Indexing.
- Does not require DMC app.

- `INIT_SHCLUSTERING_SHCDEPLOYER` - set uri to Search Head Cluster deployer. Defaults to `https://shc-deployer:8089`.

Before starting Splunk after applying configuration changes waits for the
Search Head Cluster Deployer defined with `INIT_SHCLUSTERING_SHCDEPLOYER`.

##### Data collector

- Does not require KVStore.
- Does not require Splunk Web.
- Does not require Indexing.
- Does not require DMC app.

- `INIT_ADD_UDP_PORT` - add listening on port defined with this variable, sets `connection_host = dns`,
    `index = splunkcluster` and register this as a service in consul with name `syslog`.
- `INIT_ADD_UDP_PORT_INDEX` - specify index for upd port. Defaults to `splunkcluster`.
- `INIT_REGISTER_PUBLIC_HTTP_EVENT_COLLECTOR` - register this instance as public HEC service in consul,
    will be published with load balancer.

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
- `8010` - redirects to Cluster Master.
- `8050` - redirects to consul.
- `8088` - lb for public HEC

> NOTE: consul is not secured by default.

### Consul image

Image based on `consul:v0.6.4`.

## Use it

### Deploy

#### On docker instance

> NOTE2: If you are using Docker for Mac - it allocates just 2Gb by default, not enough for this demo. Set more. Maybe 8Gb.

```
cd ./examples/docker
```

This folder has two docker-compose files. One which does not require License Master and Splunk Enterprise License
`docker-compose.yml` and second is an extension for the first one, which adds License Master node. `Makefile` in this folder
deals with how `docker-compose` needs to be invoked.

##### If you do not have a License

Build images.

```
make build
```

Deploy instances.

```
make deploy
```

Watch for status of deployment:
- Open `http://<docker>:8500` to watch for all green services and hosts.
- Watch for `docker-compose logs -f shc-member` for the line `Successfully bootstrapped this node as the captain with the given servers.`.
    This will mean that SHC is bootstrapped.
- Open Cluster Master web on `http://<docker>:8010` and check `Indexer Clustering: Master Node` page
    that Indexes are replicated and ready for search.
- Open SHC on `http://<docker>:8000` and check that you see logs from all instances `index="_internal" | stats count by host`.

You can scale up later with

```
docker-compose -f docker-compose.yml scale cluster-slave=5
```

To clean use

```
make clean
```

##### If you have a Splunk Enterprise License

If you have Splunk Enterprise License copy it in this folder (make sure that license files have extension `*.lic`).

Build images.

```
make build-lm
```

Deploy instances. This command copies license files to the license master node, deploys 3 SHC Members and 3 Indexer Cluster Slaves.
Command will fail if you don't have license files in current folder.

```
make deploy-lm
```

Watch for status of deployment:
- Open `http://<docker>:8500` to watch for all green services and hosts.
- Watch for `docker-compose logs -f shc-member` for the line `Successfully bootstrapped this node as the captain with the given servers.`.
    This will mean that SHC is bootstrapped.
- Open Cluster Master web on `http://<docker>:8010` and check `Indexer Clustering: Master Node` page
    that Indexes are replicated and ready for search.
- Open SHC on `http://<docker>:8000` and check that you see logs from all instances `index="_internal" | stats count by host`.

You can scale up later with

```
docker-compose -f docker-compose.yml -f docker-compose.license-master.yml scale cluster-slave=5
```

To clean use

```
make clean-lm
```

#### On docker swarm

> NOTE1: Splunk Enterprise License is required
> NOTE2: You have to use docker registry to be sure that each instance will have access to images built by you.
> Or you can publish image on every swarm instance manually. Specify path to your registry with
> environment variable `SPLUNK_CLUSTER_DOCKER_IMAGE_PATH=registry.yourcompany.com/$USER`

```
cd ./examples/docker-swarm-mode
```

Copy Splunk Enterprise license (if you have) in this folder (make sure that license files have extension `*.lic`).

Prepare swarm. This command will create 5 docker-machine instances in VirtualBox. 3 of them will be used in Docker Swarm
right away, 2 can be added later

```
make setup
```

If you want to use custom build, use next command. 
Build images. This command will build images and publish to local registry.

```
SPLUNK_CLUSTER_DOCKER_IMAGE_PATH=registry.yourcompany.com/$USER make build
```

Login to your registry

```
docker login registry.yourcompany.com
```

Publish images to your registry

```
SPLUNK_CLUSTER_DOCKER_IMAGE_PATH=registry.yourcompany.com/$USER make push
```

Deploy cluster.

```
SPLUNK_CLUSTER_DOCKER_IMAGE_PATH=registry.yourcompany.com/$USER make deploy
```

After SHC will be bootstrapped, if you will change password to `changed` you can invoke next command to automatically
add them as search peers to the Cluster Master (if you want to setup DMC)

```
SPLUNK_CLUSTER_DOCKER_IMAGE_PATH=registry.yourcompany.com/$USER make demo-add-peers
```

You can also add two more nodes to the Swarm cluster by invoking

```
SPLUNK_CLUSTER_DOCKER_IMAGE_PATH=registry.yourcompany.com/$USER make setup-add-2
```

To clean splunk cluster (including volumes) use

```
SPLUNK_CLUSTER_DOCKER_IMAGE_PATH=registry.yourcompany.com/$USER make clean-all
```

To clean images (in case if you want to rebuild)

```
SPLUNK_CLUSTER_DOCKER_IMAGE_PATH=registry.yourcompany.com/$USER make clean-images
```

To remove all docker machines use

```
SPLUNK_CLUSTER_DOCKER_IMAGE_PATH=registry.yourcompany.com/$USER make setup-clean
```

#### On kubernetes

> TODO

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
- [ ] Deployment Server listen on 8089, HAProxy forwards TCP, should we implement it better?
- [ ] Encrypt consul communication
- [ ] CA Authority. Do not skip certificate verification.
- [ ] Check if there are better way to configure SSO (including trustedIP)
- [ ] On SHC we should log IP addresses with "tools.proxy.on = True"
- [ ] Upgrade to consul-template 0.16.0 rtm.
- [ ] Secure by default `8500`.
- [ ] SHC Autobootstrap should support removed members.
- [ ] Possible issues with permissions.
- [ ] Verify that LB works while adding/removing members
- [ ] LDAP

## Used tools

- [consul](https://www.consul.io)
- [consul-template](https://github.com/hashicorp/consul-template)
- [haproxy](http://www.haproxy.org)
- [supervisor](http://supervisord.org)
- [supervisor-logging](https://github.com/infoxchange/supervisor-logging)
