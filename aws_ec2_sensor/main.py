from datetime import datetime, date, timedelta
import json
from functools import wraps
from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory, abort, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os
import jwt
import zipfile


SECRET_KEY = os.environ.get('SECRET_KEY')
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
server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'gyroscope.db')

server.config['SQLALCHEMY_BINDS'] = {
    'db2': 'sqlite:///' + os.path.join(base_dir, f'db/gyroscopeuncalibrated.db'),
    'db3': 'sqlite:///' + os.path.join(base_dir, f'db/accelerometer.db'),
    'db4': 'sqlite:///' + os.path.join(base_dir, f'db/accelerometeruncalibrated.db'),
    'db5': 'sqlite:///' + os.path.join(base_dir, f'db/location.db'),
    'db6': 'sqlite:///' + os.path.join(base_dir, f'db/barometer.db'),
    'db7': 'sqlite:///' + os.path.join(base_dir, f'db/gravity.db'),
    'db8': 'sqlite:///' + os.path.join(base_dir, f'db/orientation.db')
}

db = SQLAlchemy()
db.init_app(server)

## CREATE TABLE IN DB
class Gyroscope(db.Model):
    __tablename__ = "gyroscope"
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.Integer)
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    z = db.Column(db.Float)    
    date = db.Column(db.Date, default=date.today)
    username = db.Column(db.String(100))  
    
      
class GyroscopeUncalibrated(db.Model):
    __bind_key__ = 'db2'
    __tablename__ = "gyroscopeuncalibrated"
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.Integer)
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    z = db.Column(db.Float)
    date = db.Column(db.Date, default=date.today)
    username = db.Column(db.String(100))    
    
    
class Accelerometer(db.Model):
    __bind_key__ = 'db3'
    __tablename__ = "accelerometer"
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.Integer)
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    z = db.Column(db.Float)
    date = db.Column(db.Date, default=date.today)
    username = db.Column(db.String(100))      
    

class AccelerometerUncalibrated(db.Model):
    __bind_key__ = 'db4'
    __tablename__ = "accelerometeruncalibrated"
    id = db.Column(db.Integer, primary_key=True)    
    time = db.Column(db.Integer)
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    z = db.Column(db.Float)
    date = db.Column(db.Date, default=date.today)
    username = db.Column(db.String(100)) 
    
    
class Location(db.Model):
    __bind_key__ = 'db5'
    __tablename__ = "location"
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.Integer)
    bearingAccuracy = db.Column(db.Float)
    speedAccuracy = db.Column(db.Float)
    verticalAccuracy = db.Column(db.Float)
    horizontalAccuracy = db.Column(db.Float)
    speed = db.Column(db.Float)
    bearing = db.Column(db.Float)
    altitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
    date = db.Column(db.Date, default=date.today)
    username = db.Column(db.String(100))  
    
    
class Barometer(db.Model):
    __bind_key__ = 'db6'
    __tablename__ = "barometer"
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.Integer)
    relativeAltitude = db.Column(db.Float)
    pressure = db.Column(db.Float)
    date = db.Column(db.Date, default=date.today)
    username = db.Column(db.String(100))  
        
        
class Gravity(db.Model):
    __bind_key__ = 'db7'
    __tablename__ = "gravity"
    id = db.Column(db.Integer, primary_key=True)    
    time = db.Column(db.Integer)
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    z = db.Column(db.Float)
    date = db.Column(db.Date, default=date.today)
    username = db.Column(db.String(100))   
    
    
class Orientation(db.Model):
    __bind_key__ = 'db8'
    __tablename__ = "orientation"
    id = db.Column(db.Integer, primary_key=True)    
    time = db.Column(db.Integer)
    qx = db.Column(db.Float)
    qy = db.Column(db.Float)
    qz = db.Column(db.Float)
    qw = db.Column(db.Float)
    roll = db.Column(db.Float)
    pitch = db.Column(db.Float)
    yaw = db.Column(db.Float)
    date = db.Column(db.Date, default=date.today)
    username = db.Column(db.String(100))    
         
    
with server.app_context():
    db.create_all()
    db.create_all(bind_key='db2')
    db.create_all(bind_key='db3')
    db.create_all(bind_key='db4')
    db.create_all(bind_key='db5')
    db.create_all(bind_key='db6')
    db.create_all(bind_key='db7')
    db.create_all(bind_key='db8')
    
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
def data():  # listens to the data streamed from the sensor logger
    if request.method == 'POST':
        data = json.loads(request.data)['payload']
        news = []
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
                                username='test')
                news.append(new)                                
                continue
            if item_name == 'gyroscopeuncalibrated':
                new = GyroscopeUncalibrated(time=item_time,
                                            x=item_values['x'],
                                            y=item_values['y'],
                                            z=item_values['z'],
                                            date=datetime.fromtimestamp(item_time/10e8).date(),
                                            username='test')
                news.append(new)                                            
                continue
            if item_name == 'accelerometer':
                new = Accelerometer(time=item_time,
                                    x=item_values['x'],
                                    y=item_values['y'],
                                    z=item_values['z'],
                                    date=datetime.fromtimestamp(item_time/10e8).date(),
                                    username='test')
                news.append(new)                                    
                continue
            if item_name == 'accelerometeruncalibrated':
                new = AccelerometerUncalibrated(time=item_time,
                                                x=item_values['x'],
                                                y=item_values['y'],
                                                z=item_values['z'],
                                                date=datetime.fromtimestamp(item_time/10e8).date(),
                                                username='test')
                news.append(new)                                                 
            if item_name == 'location':
                new = Location(time=item_time,
                                bearingAccuracy=item_values['bearingAccuracy'],
                                speedAccuracy=item_values['speedAccuracy'],
                                verticalAccuracy=item_values['verticalAccuracy'],
                                horizontalAccuracy=item_values['horizontalAccuracy'],
                                speed=item_values['speed'],
                                bearing=item_values['bearing'],
                                altitude=item_values['altitude'],
                                longitude=item_values['longitude'],
                                latitude=item_values['latitude'],
                                date=datetime.fromtimestamp(item_time/10e8).date(),
                                username='test')
                news.append(new)                                
            if item_name == 'gravity':
                new = Gravity(time=item_time,
                                x=item_values['x'],
                                y=item_values['y'],
                                z=item_values['z'],
                                date=datetime.fromtimestamp(item_time/10e8).date(),
                                username='test')
                news.append(new)                                
            if item_name == 'orientation':
                new = Orientation(time=item_time,
                                    qz=item_values['qz'],
                                    qy=item_values['qy'],
                                    qx=item_values['qx'],
                                    qw=item_values['qw'],
                                    roll=item_values['roll'],
                                    pitch=item_values['pitch'],
                                    yaw=item_values['yaw'],
                                    date=datetime.fromtimestamp(item_time/10e8).date(),
                                    username='test')
                news.append(new)    
        db.session.add_all(news)
        db.session.commit()                                                                                    
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

    TABLES = [Gyroscope, GyroscopeUncalibrated, Accelerometer, AccelerometerUncalibrated, Location, Barometer, Gravity, Orientation]
    TABLE_NAMES = ['Gyroscope', 'GyroscopeUncalibrated', 'Accelerometer', 'AccelerometerUncalibrated', 'Location', 'Barometer', 'Gravity', 'Orientation']
    
    for table, table_name in zip(TABLES, TABLE_NAMES):
        data = db.session.query(table).all()
        columns = table.__table__.columns.keys()

        results = pd.DataFrame([tuple(getattr(d, column) for column in columns) for d in data], columns=columns)
        if date_to_get != 'all':
            results = results[results.date == date_to_get]
        results.to_csv(f'./static/{date_to_get}/{table_name}.csv', index=False)
    
    zip_folder(f'static/{date_to_get}', f'static/{date_to_get}.zip')  
    
    return send_from_directory(f'static/', f'{date_to_get}.zip')
                
        
if __name__ == "__main__":
    import socket
    hostname = socket.gethostname()
    print(socket.gethostbyname(hostname))
    
	# run the web server
    server.run(port=8000, host="0.0.0.0")  