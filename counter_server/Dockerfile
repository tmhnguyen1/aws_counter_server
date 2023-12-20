FROM ubuntu

RUN apt-get update -y
RUN apt-get install python3-pip -y
RUN apt-get install gunicorn3 -y

RUN mkdir /app

COPY requirements.txt .
COPY counter_server /app/

RUN pip3 install -r requirements.txt

WORKDIR /app/
EXPOSE 8000

CMD [ "gunicorn3", "-b", "0.0.0.0:8000", "main:server" ]