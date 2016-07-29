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
	minikube start --cpus=6 \
		--disk-size=200g \
		--memory=9216 \
		--vm-driver="virtualbox" \
		--insecure-registry=$$(docker-machine ip registry)
	kubectl config set-context minikube