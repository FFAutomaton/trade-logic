#!/bin/bash

DOCKER_ID=$(docker ps -aqf "name=trade-bot")
docker stop $DOCKER_ID
docker build --rm -t trade-bot ./
docker run -t -i -d --rm \
    --name trade-bot -v /Users/sevki/Documents/repos/turkish-gekko-organization/trade-logic/trade-bot-logs:/output \
     -v /Users/sevki/Documents/repos/turkish-gekko-organization/trade-logic/coindata/ETHUSDT.db:/app/coindata/ETHUSDT.db \
     trade-bot
