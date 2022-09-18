#!/bin/bash

DOCKER_ID=$(docker ps -aqf "name=trade-bot")
docker stop $DOCKER_ID
docker build --rm -t trade-bot ./
docker run -t -i -d --rm \
    --name trade-bot -v /home/ubuntu/trade-logic/trade-bot-logs:/output \
     -v /home/ubuntu/trade-logic/coindata/ETHUSDT.db:/app/coindata/ETHUSDT.db \
     trade-bot
