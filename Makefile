docker-build:
	docker build -t ghcr.io/fybrik/fybrik-workload-job:0.0.0 .

docker-push:
	docker image push ghcr.io/fybrik/fybrik-workload-job:0.0.0
