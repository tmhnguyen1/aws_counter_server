from datetime import datetime, date
import json
from collections import deque
from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory, abort, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from sqlalchemy import create_engine, func
import pickle
import os

from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt


label_list = ['1. Harsh acceleration',\
            '2. Harsh deceleration',\
            '3. Sharp cornering',\
            '5. Tailgating',\
            # '6. Phone handling',\
            '7. Lane switch']
SECRET_KEY = os.environ.get('SECRET_KEY')

server = Flask(__name__)
base_dir = os.path.abspath(os.path.dirname(__file__))

server.config['SECRET_KEY'] = SECRET_KEY
server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'db/labels.db')
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(server)

login_manager = LoginManager()
login_manager.init_app(server)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# counter_label: admin_only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*arg, **kwargs):
        if current_user.id not in [1,2]:
            return abort(403)
        else:
            return f(*arg, **kwargs)
    return decorated_function


## CREATE TABLE IN DB
class Counter(db.Model):
    __tablename__ = "counter"
    id = db.Column(db.Integer, primary_key=True)
    label_no = db.Column(db.Integer)
    label_desc = db.Column(db.String(200))
    count_val = db.Column(db.Integer)
    date = db.Column(db.Date, default=date.today)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_name = db.Column(db.String(100))
    
    
class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))  # hashed password


# # Line below only required once, when creating DB
# def create_initial_records():
#     counters = [Counter(label_no=i, label_desc=label_list[i], count_val=0, timestamp=datetime.now(), date=datetime.today(), user_name='test') for i in range(len(label_list))]
#     db.session.bulk_save_objects(counters)
#     db.session.commit()    

# def create_users(user_list):
#     for record in user_list:
#         print(record)
#         username, password = record
#         hashed_salty_password = generate_password_hash(password,
#                                                         salt_length=8)
#         new_user = User(password=hashed_salty_password,
#                         username=username) 
#         db.session.add(new_user)
#         db.session.commit()

with server.app_context():
    db.create_all()
    # create_initial_records()
    # create_users([])
    # meta = db.metadata
    # meta.reflect(bind=db.engine)
    # print(meta.tables.keys())


@server.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('counter', user_name=username))
            else:
                flash('Invalid Password')
                return redirect(url_for('login'))
        else:
            flash('Invalid Username')
            return redirect(url_for('login'))
    return render_template("login.html")


@server.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@server.route('/counter/<user_name>', methods=['GET', 'POST'])
@login_required
def counter(user_name):
    counters = db.session.query(Counter.label_no, Counter.label_desc, Counter.count_val, func.max(Counter.timestamp), Counter.date).group_by(Counter.label_no).all()
    if request.method == 'POST':
        counter_id = int(request.form.get('counter_id'))
        timestamp = datetime.fromtimestamp(float(request.form.get('timestamp')) / 1000)
        button_type = request.form.get('buttontype')
        counter = Counter.query.filter(Counter.label_no == counter_id).order_by(Counter.timestamp.desc()).first()
        if counter:
            # print('pressed', timestamp, timestamp.date(), button_type, counter.label_no, counter.count_val, counter.date)
            if button_type == 'add':
                count_val = counter.count_val + 1
            else:
                count_val = counter.count_val - 1
            timestamp = Counter(label_no=counter_id,
                                label_desc=label_list[counter_id],
                                count_val=count_val,
                                timestamp=timestamp,
                                date=timestamp.date(),
                                user_name=user_name)
            db.session.add(timestamp)
            db.session.commit()
    return render_template('counter.html', counters=counters, user_name=user_name, logged_in=current_user.is_authenticated)  



@server.route('/download_counter/<date_to_get>')
@admin_only
def download_counter(date_to_get):
    # date_to_get: "YYYY-mm-dd"
    sql_engine = create_engine(os.path.join('sqlite:///' + os.path.join(base_dir, 'db/labels.db')), echo=False)
    results = pd.read_sql_query("SELECT * FROM counter", sql_engine)
    if date_to_get != 'all':
        results = results[results.date == date_to_get]
    results.to_csv(f'./static/files/counter_data/counter_{date_to_get}.csv', index=False)
    return send_from_directory(directory='static', path=f'files/counter_data/counter_{date_to_get}.csv')


######################################
#######  Sensor logger ###############
# Decorator function to check for authentication
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
@requires_authentication
def data(decoded_token):  # listens to the data streamed from the sensor logger
	if str(request.method) == "POST":
		data = json.loads(request.data)
		print(f'received data: {data["payload"]}')
		timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
		date_to_get = datetime.now().strftime('%Y-%m-%d')
		if not os.path.exists(f'static/files/sensor_data/{date_to_get}'):
			os.mkdir(f'static/files/sensor_data/{date_to_get}')
		filename = f'static/files/sensor_data/{date_to_get}/{timestamp}.pkl'
		with open(filename, 'wb') as f:
			pickle.dump(data['payload'], f)		
	return "success"


if __name__ == "__main__":
	# run the web server
    print(SECRET_KEY)
    server.run(port=8000, host="0.0.0.0", debug=True)