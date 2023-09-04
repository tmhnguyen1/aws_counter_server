from datetime import datetime, date, timedelta
import json
from collections import deque
from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory, abort, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from sqlalchemy import create_engine, func
from sqlalchemy.exc import SQLAlchemyError
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
login_manager.login_view = 'login'
login_manager.refresh_view = 'logout'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# @server.before_request
# def before_request():
#     session.permanent = True
#     server.permanent_session_lifetime = timedelta(minutes=30)


# admin_only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*arg, **kwargs):
        if current_user.id not in [1, 2]:
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
    timestamp = db.Column(db.Float)
    username = db.Column(db.String(100))
    
    
class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))  # hashed password


def create_initial_records(username):
    counters = [Counter(label_no=i, label_desc=label_list[i], count_val=0, timestamp=datetime.now().timestamp()*10e8, date=datetime.today(), username=username) for i in range(len(label_list))]
    db.session.bulk_save_objects(counters)
    db.session.commit()    


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
                return redirect(url_for('counter', username=username))
            else:
                flash('Invalid Password')
                return redirect(url_for('login'))
        else:
            flash('Invalid Username')
            return redirect(url_for('login'))
    return render_template("login.html")


@server.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('You already signed up! Please log in.')
            return redirect('login')
        else:
            hashed_salty_password = generate_password_hash(password,
                                                        salt_length=8)
            new_user = User(username=username,
                            password=hashed_salty_password) 
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            create_initial_records(username)
            return redirect(url_for('counter', username=username))
    return render_template("register.html")


@server.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return render_template('logout.html')


@server.route('/counter/<username>', methods=['GET', 'POST'])
@login_required
def counter(username):
    subquery = db.session.query(Counter.label_no, Counter.label_desc, Counter.count_val, func.max(Counter.count_val), Counter.date).group_by(Counter.label_no, Counter.username).having(Counter.username == username).subquery()
    counters = db.session.query(subquery).all()
    if request.method == 'POST':
        counter_id = int(request.form.get('counter_id'))
        timestamp = float(request.form.get('timestamp'))*10e5
        date = datetime.fromtimestamp(timestamp / 10e8).date()
        button_type = request.form.get('buttontype')
        counter = Counter.query.filter(Counter.label_no == counter_id, Counter.username == username).order_by(Counter.count_val.desc()).first()
        # print(counter.username, counter.count_val, counter.timestamp, counter.label_desc)
        if counter:
            # print('pressed', timestamp, timestamp.date(), button_type, counter.label_no, counter.count_val, counter.date)
            if button_type == 'add':
                count_val = counter.count_val + 1
            else:
                count_val = counter.count_val - 1
            new_record = Counter(label_no=counter_id,
                                label_desc=label_list[counter_id],
                                count_val=count_val,
                                timestamp=timestamp,
                                date=date,
                                username=username)
            db.session.add(new_record)
            db.session.commit()
    return render_template('counter.html', counters=counters, username=username)  


@server.route('/offline', methods=['POST'])
@login_required
def process_offline_data():
    click_data = request.form.get('click_data')
    
    data_pairs = click_data.split('&')
    click_info = {}
    for pair in data_pairs:
        key, value = pair.split('=')
        click_info[key] = value
    
    timestamp = float(click_info.get('timestamp')) * 10e5
    date = datetime.fromtimestamp(timestamp / 10e8).date()
    counter_id = int(click_info.get('counter_id'))
    button_type = click_info.get('buttontype')
    username = click_info.get('username')
    
    counter = Counter.query.filter(Counter.label_no == counter_id, Counter.username == username).order_by(Counter.count_val.desc()).first()
    if counter:
        # print('pressed', timestamp, timestamp.date(), button_type, counter.label_no, counter.count_val, counter.date)
        if button_type == 'add':
            count_val = counter.count_val + 1
        else:
            count_val = counter.count_val - 1
        new_record = Counter(label_no=counter_id,
                            label_desc=label_list[counter_id],
                            count_val=count_val,
                            timestamp=timestamp,
                            date=date,
                            username=username)
        db.session.add(new_record)
        db.session.commit()   
    return 'OK'


@server.route('/download_counter/<date_to_get>')
@admin_only
def download_counter(date_to_get):
    # date_to_get: "YYYY-mm-dd"
    data = db.session.query(Counter).all()
    results = pd.DataFrame([(d.id, d.label_no, d.label_desc, d.count_val, d.date, d.timestamp, d.username) for d in data],
                           columns=['id', 'label_no', 'label_desc', 'count_val', 'date', 'timestamp', 'username'])
    if date_to_get != 'all':
        results = results[results.date == date_to_get]
    os.makedirs('./static/files/counter_data/', exist_ok=True)
    results.to_csv(f'./static/files/counter_data/counter_{date_to_get}.csv', index=False)
    return send_from_directory('static/files/counter_data/', f'counter_{date_to_get}.csv')


@server.route('/delete/<user_id>')
@admin_only
def delete(user_id):
    try:
        user = User.query.get_or_404(user_id)
        # Delete records in the other table with the same user_id (if it exists)
        try:
            Counter.query.filter_by(user_id=user.username).delete()
        except SQLAlchemyError:
            pass  # Handle the error or skip the deletion if the table does not exist
        db.session.delete(user)
        db.session.commit()
        return 'User and related records deleted successfully', 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return 'An error occurred while deleting the user', 500   


@server.route('/users', methods=['GET'])
@admin_only
def list_users():
    users = User.query.all()
    return render_template('user.html', users=users)


if __name__ == "__main__":
	# run the web server
    server.run(port=8000, host="0.0.0.0", debug=True)