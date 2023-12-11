#!/bin/bash

docker-compose build
docker-compose up -d
container_id=$(docker ps --filter "name=talco" --format "{{.ID}}")
docker logs -f $container_id
#docker exec -it $container_id /bin/bash