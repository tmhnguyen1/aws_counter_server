FROM ubuntu

RUN apt-get update -y
RUN apt-get -y install sudo
RUN sudo apt update -y
RUN sudo apt install aws
RUN sudo apt install cron

RUN mkdir /app
COPY sync.sh /app/sync.sh
RUN chnmod +x /app/sync.sh

COPY root /var/spool/cron/crontabs/root

RUN mkdir /app/counter_server/db

ENTRYPOINT ["/usr/sbin/crond","-l","2","-f"]