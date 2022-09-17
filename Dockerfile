# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

ENV WORKDIR=/app
WORKDIR ${WORKDIR}

RUN apt-get update && apt-get upgrade -y && apt-get install -y git && apt-get install -y cron

#RUN apt-get install -y python3-dev
#RUN apt install -y gcc
#RUN apt install -y g++

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY --chown=1001 . .
RUN chmod +x $WORKDIR/main.py $WORKDIR/bash_scripts/run.sh $WORKDIR/bash_scripts/entrypoint.sh

CMD ["bash"]
ENTRYPOINT $WORKDIR/bash_scripts/entrypoint.sh

