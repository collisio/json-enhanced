#!/bin/bash

echo "Building the container..."
echo

docker stop json-queries > /dev/null 2>&1
docker rm json-queries > /dev/null 2>&1
docker image prune --filter label=stage=builder -f > /dev/null 2>&1

ERR=$(docker build --force-rm -t json-queries . 2>&1 > /dev/null) || echo "ERRORS IN BUILD: $ERR" && \
if [[ $# -eq 0 ]]
then
    echo "==== Building without volume ===="
    echo
    docker run --rm --name json-queries -v /etc/localtime:/etc/localtime:ro -it json-queries
else
    echo "==== Building with volume ===="
    echo "mounted at /mnt$1"
    echo
    docker run --rm --name json-queries -v $1:/mnt/$1 -v /etc/localtime:/etc/localtime:ro -it json-queries
fi