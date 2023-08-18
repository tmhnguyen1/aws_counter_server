import dash
from dash.dependencies import Output, Input
from dash import dcc, html, dcc
from datetime import datetime
import json
import plotly.graph_objs as go
from collections import deque
from flask import Flask, request
import pickle
import os
import boto3


# Create an S3 client
s3_client = boto3.client('s3')

# Set the source file or directory path on the EC2 instance
SOURCE_PATH = '/root/learning/data/'

# Set the destination S3 bucket and key prefix
BUCKET_NAME = 'lalamove-apas'
DESTINATION_PREFIX = 'data'
 

# Upload the data to S3
def upload_to_s3(filename):
    if os.path.isfile(SOURCE_PATH + filename):
        # Upload a single file
        s3_client.upload_file(SOURCE_PATH, BUCKET_NAME, f"{DESTINATION_PREFIX}/{os.path.basename(SOURCE_PATH)}")
    elif os.path.isdir(SOURCE_PATH):
        # Upload a directory and its contents recursively
        for root, dirs, files in os.walk(SOURCE_PATH):
            for file in files:
                local_path = os.path.join(root, file)
                s3_key = os.path.relpath(local_path, SOURCE_PATH)
                s3_object_key = f"{DESTINATION_PREFIX}/{s3_key}"
                s3_client.upload_file(local_path, BUCKET_NAME, s3_object_key)
    else:
        print("Invalid source path. Please provide a valid file or directory path.")


server = Flask(__name__)
app = dash.Dash(__name__, server=server)


@server.route("/")
def home():
    return '<h1>Succesffully access the web server<h1>'

@server.route("/data", methods=["POST"])
def data():  # listens to the data streamed from the sensor logger
	if str(request.method) == "POST":
		print(f'received data: {request.data["payload"][0]}')
		data = json.loads(request.data)
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
	app.run_server(port=8000, host="0.0.0.0")