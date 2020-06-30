from flask import Flask, request, abort
from flask_mail import Mail, Message
from json import loads, dumps
from flask_cors import CORS
import requests
import redis
import os
from pytz import timezone
from datetime import datetime
from constants import ADDRESS, PASSWORD
from notify import get_data, get_valid_hours 
from helpers import write_location_string

r = redis.from_url(os.environ.get('REDIS_URL'))

app = Flask(__name__)
cors = CORS(app)
mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": ADDRESS,
    "MAIL_PASSWORD": PASSWORD 
}

app.config.update(mail_settings)
mail = Mail(app)

@app.route('/', methods=['GET'])
def index():
    return 'Welcome to the Conditions API'

@app.route('/update', methods=['POST'])
def update():
    if not request.json:
        abort(400)
    email = request.json['email']
    to_delete = request.json['name']
    data = loads(r.get(email))
    del request.json['email']
    new_locations = [d for d in data['locations'] if d['name']!=to_delete]+[request.json]

    data['locations'] = new_locations
    r.set(email, dumps(data))

    return data

@app.route('/delete', methods=['POST'])
def delete():
    if not request.json:
        abort(400)

    email = request.json['email']
    to_delete = request.json['name']
    data = loads(r.get(email))
    new_locations = [d for d in data['locations'] if d['name']!=to_delete]
    data['locations'] = new_locations

    r.set(email, dumps(data))
    return data

@app.route('/add', methods=['POST'])
def add():
    if not request.json:
        abort(400)

    email = request.json['email']
    data = loads(r.get(email))
    del request.json['email']
    data['locations'].append(request.json)

    r.set(email, dumps(data))
    return data

@app.route('/login', methods=['POST'])
def login():
    if not request.json:
        abort(400)
    email = request.json['email']
    user = r.get(email)
    if user is None:
        user = {'locations': [], 'email': email}
        r.set(email, dumps(user))

    return user

@app.route('/notify', methods=['GET'])
def notify():
    for key in r.scan_iter():
        user_data = loads(r.get(key))
        for data in user_data['locations']:
            weather_data = get_data(data)
            if weather_data:
                valid_hours = get_valid_hours(data, weather_data)
                location_string = write_location_string(valid_hours)
                message= f"Location: {data['name']}\n\n"
                message+=location_string
                with app.app_context():
                    msg = Message(subject="Conditions Application notification for the week",
                            sender=app.config.get("MAIL_USERNAME"),
                            recipients=[user_data['email']], # replace with your email for testing
                                body="This is a test email I sent with Gmail and Python!")
                    mail.send(msg)


if __name__ == '__main__':
    app.run()
