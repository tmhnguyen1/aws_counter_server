from datetime import datetime, date, timedelta
import json
from functools import wraps
from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory, abort, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os
import jwt
import zipfile


SECRET_KEY = 'anything' #os.environ.get('SECRET_KEY')
SENSOR_NAMES = [
    'gyroscope',
    'gyroscopeuncalibrated',
    'accelerometer',
    'accelerometeruncalibrated',
    'location',
    'barometer',
    'gravity',
    'orientation'
]
    
    
server = Flask(__name__)
base_dir = os.path.abspath(os.path.dirname(__file__))

server.config['SECRET_KEY'] = SECRET_KEY
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

server.config['SQLALCHEMY_BINDS'] = {
    'db1': 'sqlite:///' + os.path.join(base_dir, f'db/gyroscope.db'),
    'db2': 'sqlite:///' + os.path.join(base_dir, f'db/gyroscopeuncalibrated.db')#,
    # 'db3': 'sqlite:///' + os.path.join(base_dir, f'db/accelerometer.db'),
    # 'db4': 'sqlite:///' + os.path.join(base_dir, f'db/accelerometeruncalibrated.db'),
    # 'db5': 'sqlite:///' + os.path.join(base_dir, f'db/location.db'),
    # 'db6': 'sqlite:///' + os.path.join(base_dir, f'db/barometer.db'),
    # 'db7': 'sqlite:///' + os.path.join(base_dir, f'db/gravity.db'),
    # 'db8': 'sqlite:///' + os.path.join(base_dir, f'db/orientation.db')
}

db = SQLAlchemy()
db.init_app(server)

db1 = SQLAlchemy(bind_key='db1')
db2 = SQLAlchemy(bind_key='db2')
# db3 = SQLAlchemy(server, bind_key='db3')
# db4 = SQLAlchemy(server, bind_key='db4')
# db5 = SQLAlchemy(server, bind_key='db5')
# db6 = SQLAlchemy(server, bind_key='db6')
# db7 = SQLAlchemy(server, bind_key='db7')
# db8 = SQLAlchemy(server, bind_key='db8')

db1.init_app(server)
db2.init_app(server)

## CREATE TABLE IN DB
class Gyroscope(db1.Model):
    __bind_key__ = 'db1'
    __tablename__ = "gyroscope"
    id = db1.Column(db1.Integer, primary_key=True)
    time = db1.Column(db1.Integer)
    x = db1.Column(db1.Float)
    y = db1.Column(db1.Float)
    z = db1.Column(db1.Float)    
    date = db1.Column(db1.Date, default=date.today)
    username = db1.Column(db1.String(100))  
    
      
class GyroscopeUncalibrated(db2.Model):
    __bind_key__ = 'db2'
    __tablename__ = "gyroscopeuncalibrated"
    id = db2.Column(db2.Integer, primary_key=True)
    time = db2.Column(db2.Integer)
    x = db2.Column(db2.Float)
    y = db2.Column(db2.Float)
    z = db2.Column(db2.Float)
    date = db2.Column(db2.Date, default=date.today)
    username = db2.Column(db2.String(100))    
    

######################################
#######  Sensor logger ###############
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


@server.route("/data", methods=["POST"])
# @requires_authentication
def data(decoded_token):  # listens to the data streamed from the sensor logger
    if request.method == 'POST':
        data = json.loads(request.data)['payload']
        for item in data:
            item_name = item['name']
            item_time = item['time']
            item_values = item['values']
            if item_name == 'gyroscope':
                new = Gyroscope(time=item_time,
                                x=item_values['x'],
                                y=item_values['y'],
                                z=item_values['z'],
                                date=datetime.fromtimestamp(item_time/10e8).date(),
                                username=decoded_token)
                db1.session.add(new)
                db1.session.commit()
                continue
            if item_name == 'gyroscopeuncalibrated':
                new = GyroscopeUncalibrated(time=item_time,
                                            x=item_values['x'],
                                            y=item_values['y'],
                                            z=item_values['z'],
                                            date=datetime.fromtimestamp(item_time/10e8).date(),
                                            username=decoded_token)
                db2.session.add(new)
                db2.session.commit()
                continue
    return 'success'


def zip_folder(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))


@server.route('/download/<date_to_get>')
def download_data(date_to_get):
    # date_to_get: "YYYY-mm-dd" or "all"
    
    if not os.path.exists(f'static/{date_to_get}'):
        os.mkdir(f'static/{date_to_get}')
    
    data = db1.session.query(Gyroscope).all()
    results = pd.DataFrame([(d.id, d.time, d.x, d.y, d.z, d.date, d.username) for d in data],
                           columns=['id', 'time', 'x', 'y', 'z', 'date', 'username'])
    if date_to_get != 'all':
        results = results[results.date == date_to_get]
    results.to_csv(f'./static/{date_to_get}/Gyroscope.csv', index=False)
    
    data = db2.session.query(GyroscopeUncalibrated).all()
    results = pd.DataFrame([(d.id, d.time, d.x, d.y, d.z, d.date, d.username) for d in data],
                           columns=['id', 'time', 'x', 'y', 'z', 'date', 'username'])
    if date_to_get != 'all':
        results = results[results.date == date_to_get]
    results.to_csv(f'./static/{date_to_get}/GyroscopeUncalibrated.csv', index=False)
    
    zip_folder(f'static/{date_to_get}', f'static/{date_to_get}.zip')  
    
    return send_from_directory(f'static/', f'{date_to_get}.zip')
                
        


if __name__ == "__main__":
    import socket
    hostname = socket.gethostname()
    print(socket.gethostbyname(hostname))
    
	# run the web server
    server.run(port=8000, host="0.0.0.0", debug=True)  