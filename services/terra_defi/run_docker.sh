#!/bin/bash

docker kill $(docker ps -q --filter ancestor=ftool-py_terra-defi)
git fetch && git pull
docker-compose build --no-cache terra-defi
docker run -p 5020:5020 -d ftool-py_terra-defi