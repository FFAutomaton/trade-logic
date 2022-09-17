#!/bin/bash

DOCKER_ID=$(docker ps -aqf "name=prophet-trader")
docker stop $DOCKER_ID
docker build --rm -t prophet-trader ./
docker run -t -i -d --rm \
    --name prophet-trader -v /Users/sevki/Documents/repos/trade-logic/trade-bot-logs:/output \
     -v /Users/sevki/Documents/repos/trade-logic/coindata/ETHUSDT.db:/app/coindata/ETHUSDT.db \
     prophet-trader
