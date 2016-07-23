clean:
	docker-compose kill
	docker-compose rm -v -f

build:
	docker-compose build

deploy:
	docker-compose up -d
	docker-compose scale cluster-slave=4 shc-member=3
	@echo "Use 'docker-compose logs -f cluster-master' to wait for Initialized cluster-master as Cluster Master"
