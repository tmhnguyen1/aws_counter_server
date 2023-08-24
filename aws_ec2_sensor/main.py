from datetime import datetime, date, timedelta
import json
from collections import deque
from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory, abort, jsonify, session
import pandas as pd
import pickle
import os
from functools import wraps


SECRET_KEY = os.environ.get('SECRET_KEY') #os.environ.get('SECRET_KEY')

server = Flask(__name__)
base_dir = os.path.abspath(os.path.dirname(__file__))

server.config['SECRET_KEY'] = SECRET_KEY
server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'db/labels.db')
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


def requires_authentication(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'Authorization' not in request.headers:
            return jsonify({'message': 'Authorization required'}), 401
        auth_header = request.headers.get('Authorization')
        try:
            # Extract the token from the header
            token = auth_header.split(' ')[1]  # Assuming the token is sent as "Bearer <token>"
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except IndexError:
            return jsonify({'message': 'Invalid Authorization header format'}), 401        
        return f(decoded_token, *args, **kwargs)
    return decorated


@server.route("/data/<device_id>", methods=["POST"])
# @requires_authentication
def data(device_id):  # listens to the data streamed from the sensor logger
	if str(request.method) == "POST":
		data = json.loads(request.data)
		timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
		date_to_get = datetime.now().strftime('%Y-%m-%d')
		print(f'received data: timestamp')
		if not os.path.exists(base_dir + f'/data/{device_id}/{date_to_get}'):
			os.makedirs(base_dir + f'/data/{device_id}/{date_to_get}')
		filename = base_dir + f'/data/{device_id}/{date_to_get}/{timestamp}.pkl'
		with open(filename, 'wb') as f:
			pickle.dump(data['payload'], f)		
	return "success"


if __name__ == "__main__":
    import socket
    hostname = socket.gethostname()
    print(socket.gethostbyname(hostname))
    
	# run the web server
    server.run(port=8000, host="0.0.0.0", debug=True)