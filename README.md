# Cluster-aware Splunk Enterprise docker image 

## Introduction

> NOTE: I'm working at Splunk, but this is not an official Splunk images.
> I build them in my free time when I'm not at work. I have some knowledge
> about Splunk, but you should think twice before putting them in
> production. I run these images on my own home server just for
> my personal needs. If you have any issues - feel free to open a
> [bug](https://github.com/outcoldman/docker-splunk-cluster/issues).

> Use for learning purposes.

## Version

Based on `outcoldman/splunk:6.4.2`.

* Version: `6.4.2`
* Build: `00f5bb3fa822`

## How it works

Current image has some configuration scripts (python) and predefined configurations
with some placeholders.

The main idea is simple, to use original `outcoldman` (or RelEng\official Splunk) images without any modifications to `entrypoint.sh`. On top build images for every role but just including few python scripts (`init.py` and some conf files). Invoke these scripts with `SPLUNK_CMD` command.


- docker-compose build && make clean local-up
- Wait for the cluster
- make bootstrap - to bootstrap 

## TODO:

- [ ] Secret storage for getting secrets (currently everything is in plain text from env variables)
- [ ] DMC Server (with all configurations setup automatically)
- [ ] Deployment Server
- [ ] Forwarders
 
## Bootstrap a captain example

```
docker exec -it cluster_shc-member_1 entrypoint.sh splunk bootstrap shcluster-captain -auth admin:changeme -servers_list "https://f0b64885cfa9:8089,https://c48c6a8c4d1d:8089,https://b5e331a49a11:8089"
```