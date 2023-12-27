FROM ubuntu

RUN apt-get update -y
RUN apt-get -y install sudo

# Install AWS CLI dependencies
RUN apt-get update && \
    apt-get install -y python3-pip groff && \
    pip3 install --upgrade awscli
RUN sudo apt install cron

RUN mkdir /app
COPY sync.sh /app/sync.sh
RUN chmod +x /app/sync.sh

COPY root /var/spool/cron/crontabs/root
RUN chmod 600 /var/spool/cron/crontabs/root

RUN mkdir -p /app/counter_server/db

ENTRYPOINT ["/usr/sbin/cron","-l","2","-f"]