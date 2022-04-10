#!/bin/bash

echo "Docker container has been started ..."
echo "Starting ..." >> /output/schedule.log 2>&1
python --version

# Setup a cron schedule
crontab schedule.txt
cron -f
