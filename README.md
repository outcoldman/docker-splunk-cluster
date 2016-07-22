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

## Configuration

- `INIT_SHCLUSTERING_SHCLUSTER_LABEL`


## Examples

Install app using SHC Deployer

```
docker cp ~/Downloads/splunk_app_aws shc-deployer:/opt/splunk/etc/shcluster/apps/
docker exec shc-deployer entrypoint.sh chown -R splunk:splunk /opt/splunk/etc/shcluster/apps/
docker exec shc-deployer entrypoint.sh splunk apply shcluster-bundle -restart true --answer-yes -target https://3cf08a2cb3d5:8089 -auth admin:changeme
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
 