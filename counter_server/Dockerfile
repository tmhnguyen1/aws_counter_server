FROM ubuntu

RUN sudo apt update -y
RUN sudo apt install python3 -y
RUN sudo apt install --yes python3-pip
RUN sudo apt install gunicorn3 -y

RUN mkdir /app

COPY requirements.txt .
COPY app /app/

RUN pip3 install -r requirements.txt

WORKDIR /app/
EXPOSE 8000

CMD [ "gunicorn3", "-b", "0.0.0.0:8000", "main:server" ]