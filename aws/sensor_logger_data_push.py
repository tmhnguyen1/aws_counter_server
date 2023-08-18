from datetime import datetime
import json
from collections import deque
from flask import Flask, request
import pickle
import os

server = Flask(__name__)

@server.route("/")
def home():
    return '<h1>Succesffully access the web server<h1>'

@server.route("/data", methods=["POST"])
def data():  # listens to the data streamed from the sensor logger
	if str(request.method) == "POST":
		data = json.loads(request.data)
		print(f'received data: {data["payload"]}')
		timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
		date = datetime.now().strftime('%Y-%m-%d')
		if not os.path.exists(f'../data/{date}'):
			os.mkdir(f'../data/{date}')
		filename = f'../data/{date}/{timestamp}.pkl'
		with open(filename, 'wb') as f:
			pickle.dump(data['payload'], f)		
	return "success"

if __name__ == "__main__":
	# run the web app
	server.run(port=8000, host="0.0.0.0")