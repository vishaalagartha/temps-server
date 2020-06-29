from flask import Flask, request, abort
from json import loads, dumps
from flask_cors import CORS
import requests
import redis
from pytz import timezone
from datetime import datetime
from constants import BASE_URL, API_KEY

r = redis.StrictRedis(host='localhost', port=6379, db=0)

app = Flask(__name__)
cors = CORS(app)

def get_valid_hours(data):
    valid_hours = []

    for hour in data['hourly']:
        valid = True
        for param, val in params.items():
            if param in hour:
                if val['minimum']<=hour[param] and val['maximum']>=hour[param]:
                    continue
                else:
                    valid = False
        if valid:
            timestamp = hour['dt']
            dt_object = datetime.fromtimestamp(timestamp).astimezone(timezone(time_range['time_zone']))
            h_ = int(dt_object.strftime('%H'))
            valid_hour = False
            for h in time_range['ranges']:
                if h_>=h[0] and h_<=h[1]:
                    valid_hour = {'hour': h_,
                                  'temp': hour['temp'],
                                  'humidity': hour['humidity'],
                                  'wind_speed': hour['wind_speed'],
                                  'dew_point': hour['dew_point'],
                                  'description': hour['weather'][0]['description']}
                    valid_hours.append(valid_hour)

def get_data():
    url = BASE_URL.format(location[0], location[1], APP_ID)
    r = requests.get(url)
    data = None
    if r.status_code==200:
        data = r.json()
    return data

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

if __name__ == '__main__':
    app.run()
