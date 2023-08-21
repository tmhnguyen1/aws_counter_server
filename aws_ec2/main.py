from datetime import datetime, date
import json
from collections import deque
from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from sqlalchemy import create_engine, func
import pickle
import os

label_list = ['1. Harsh acceleration',\
            '2. Harsh deceleration',\
            '3. Sharp cornering',\
            '5. Tailgating',\
            # '6. Phone handling',\
            '7. Lane switch']

server = Flask(__name__)
base_dir = os.path.abspath(os.path.dirname(__file__))

server.config['SECRET_KEY'] = 'any-secret-key-you-choose'
server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'db/labels.db')
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(server)

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

# # Line below only required once, when creating DB
# def create_initial_records():
#     counters = [Counter(label_no=i, label_desc=label_list[i], count_val=0, timestamp=datetime.now(), date=datetime.today(), user_name='test') for i in range(len(label_list))]
#     db.session.bulk_save_objects(counters)
#     db.session.commit()    

# with server.app_context():
#     db.create_all()
#     create_initial_records()

@server.route('/counter/<user_name>', methods=['GET', 'POST'])
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
    return render_template('counter.html', counters=counters, user_name=user_name)  


@server.route("/data", methods=["POST"])
def data():  # listens to the data streamed from the sensor logger
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

@server.route('/download_counter/<date_to_get>')
def download_counter(date_to_get):
    # date_to_get: "YYYY-mm-dd"
    sql_engine = create_engine(os.path.join('sqlite:///' + os.path.join(base_dir, 'db/labels.db')), echo=False)
    results = pd.read_sql_query("SELECT * FROM counter", sql_engine)
    if date_to_get != 'all':
        results = results[results.date == date_to_get]
    results.to_csv(f'./static/files/counter_data/counter_{date_to_get}.csv', index=False)
    return send_from_directory(directory='static', path=f'files/counter_data/counter_{date_to_get}.csv')


if __name__ == "__main__":
	# run the web server
	server.run(port=8000, host="0.0.0.0", debug=True)