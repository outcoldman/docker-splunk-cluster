# Table of Contents

- [Introduction](#introduction)
    - [Version](#version)
- [How it works](#how-it-works)
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

These examples depend on the custom image, which you can build using `./splunk-cluster/` folder.
This image differs from `outcoldman/splunk` with just one change.
It has special `splunk_setup.py` script, which allows to pre-configure Splunk.
This script supports several commands:

- `--wait-splunk schema://hostname:mgmt_port [re_server_role1] [re_server_role2] ... [re_server_roleN]`.
    This command will wait till specified url will reply and that `/services/server/info` will have
    all roles defined in `server_role` list.
- `--configure` - using environment variables append specific configurations. Environment variables can be
    defined in format 
    - `CONF[__{app_location}]__{conf}__{stanza}__{key}={value}` - this will append `key` with `value` under `stanza` in `conf` file
        in `local` folder under `app_location`. If `app_location` is not specified will be written in `local` folder under `$SPLUNK_HOME/etc/system/`.
    - `CONF[__{app_location}]__meta__{stanza}__{key}={value}` - metadata information will be written in `local.meta` file in
        `metadata` folder under `app_location`. If `app_location` is not specified will be written in `metadata` folder under `$SPLUNK_HOME/etc/system/`.
- `--add-licenses {folder}` - all licenses will be added from specified location. If no `*.lic` files can be find in this folder - 
    script will wait for them.
- `--shc-autobootstrap {number_of_expected_shc_members} {mgmt_uri} {local_user} {local_password} {service_discovery_url} {service_discovery_user} {service_discovery_password}`.
    Automatically bootstrap SHC when this will be `{number_of_expected_shc_members}` number of SHC members. Script will use KVStore endpoint
    specified under `{service_discovery_url}` to discover other members. `{mgmt_uri}` will be used to bootstrap members.
- `--healthcheck` - using environment variables `SPLUNK_HEALTHCHECK_{health_check_name}=schema://hostname:port` you can define
    how container will check that current container is healthy. For example to check that splunkd web server is responsive
    you can use `SPLUNK_HEALTHCHECK_SPLUNKD=https://127.0.0.1:8089`.

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

If you have Splunk Enterprise License copy it in this folder (make sure that license files have extension `*.lic`) and use
all commands with `-lm` suffix.

Build image.

```
make build[-lm]
```

Deploy instances.

```
make deploy[-lm]
```

Watch for status of deployment:
- Watch for `docker-compose logs -f shc-member` for the line `Successfully bootstrapped this node as the captain with the given servers.`.
    This will mean that SHC is bootstrapped.
- Open Cluster Master web on `http://<docker>:9000` and check `Indexer Clustering: Master Node` page
    that Indexes are replicated and ready for search.
- Open SHC member and check that you see logs from all instances `index="_internal" | stats count by host`.

To clean use

```
make clean[-lm]
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

To use Swarm you need to have access to the Docker registry, specify path to registry and path to image using

```
export SPLUNK_CLUSTER_DOCKER_IMAGE_PATH=registry.yourcompany.com/$USER
```

Login to your registry

```
docker login registry.yourcompany.com
```

Build image.

```
make build push
```

Publish image to your registry

```
make push
```

Deploy cluster.

```
make deploy
```

You can add two more nodes to the Swarm cluster by invoking

```
make setup-add-2
```

To clean splunk cluster (including volumes) use

```
make clean-all
```

To clean images (in case if you want to rebuild)

```
make clean-images
```

To download image on each docker instance

```
make download-image
```

To remove all docker machines use

```
make setup-clean
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
