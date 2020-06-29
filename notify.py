import redis
import requests
from json import loads
from pytz import timezone
from datetime import datetime
from constants import BASE_URL, API_KEY, ADDRESS, PASSWORD
from helpers import write_location_string
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def get_valid_hours(data, weather_data):
    params = {'temp': {'minimum': int(data['temp']['minimum'])+273,
                        'maximum': int(data['temp']['maximum'])+273},
              'humidity': data['humidity'],
              'wind_speed': data['windSpeed'],
              'dew_point': {'minimum': int(data['dewpoint']['minimum'])+273,
                        'maximum': int(data['dewpoint']['maximum'])+273},
              }

    time_range = {'ranges': [], 'time_zone': weather_data['timezone']}
    for t in data['timeRanges']:
        start = t['start']['hour']
        if t['start']['type']=='PM' and start!=12:
            start+=12
        end = t['end']['hour']
        if t['end']['type']=='PM' and end!=12:
            end+=12
        time_range['ranges'].append((start, end))

    valid_hours = []

    for hour in weather_data['hourly']:
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
            date = dt_object.strftime('%m/%d/%Y')
            h_ = int(dt_object.strftime('%H'))
            valid_hour = False
            for h in time_range['ranges']:
                if h_>=h[0] and h_<=h[1]:
                    valid_hour = {'date': date,
                                  'hour': h_,
                                  'temp': hour['temp'],
                                  'humidity': hour['humidity'],
                                  'wind_speed': hour['wind_speed'],
                                  'dew_point': hour['dew_point'],
                                  'description': hour['weather'][0]['description']}
                    valid_hours.append(valid_hour)
    return valid_hours

def get_data(data):
    lat = data['location']['lat']
    lng = data['location']['lng']
    url = BASE_URL.format(lat, lng, API_KEY)
    r = requests.get(url)
    weather_data = None
    if r.status_code==200:
        weather_data = r.json()
    return weather_data

def send_email(text, to, s):
    subject = 'Conditions Application notification for the week' 
    msg = MIMEMultipart()
    return 0

r = redis.StrictRedis(host='localhost', port=6379, db=0)
s = smtplib.SMTP('smtp.gmail.com', 587)
s.ehlo()
s.starttls()
s.login(ADDRESS, PASSWORD)

for key in r.scan_iter():
    user_data = loads(r.get(key))
    for data in user_data['locations']:
        weather_data = get_data(data)
        if weather_data:
            valid_hours = get_valid_hours(data, weather_data)
            location_string = write_location_string(valid_hours)
            message= f"Location: {data['name']}\n\n"
            message+=location_string
            msg = MIMEMultipart()
            msg['From']=ADDRESS
            msg['To']=user_data['email']
            msg['Subject']='Conditions App notification for the week'
            msg.attach(MIMEText(message, 'plain'))
            s.send_message(msg)
            del msg
s.quit()
