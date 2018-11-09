import configparser
from datetime import datetime
import json
import os
import requests
from csv import writer


config = configparser.ConfigParser()
config.read('/home/pi/private/config.ini')


main_api_key = config['DEFAULT']['MAIN_API_KEY']
twitter_api_key = config['DEFAULT']['TWITTER_API_KEY']

update_url = 'https://api.thingspeak.com/update?api_key='
tweet_url = 'https://api.thingspeak.com/apps/thingtweet/1/statuses/update'


def log(data):
    with open('/home/pi/logs/sensor_logs_' + get_month() + '.csv', 'a+') as f:
        csv_writer = writer(f)
        csv_writer.writerow([get_now()] + data)
        f.close()


def log_error(error):
    with open('/home/pi/logs/error_logs.txt', 'a') as f:
        f.write('{}: {}\n'.format(get_now(), str(error)))
        f.close()
    count_error(error)


def count_error(error):
    data = {}
    error_count = 0
    error_name = type(error).__name__
    with open('/home/pi/logs/errors.json', 'r') as f:
        data = json.load(f)
        error_count = data.get(error_name, 0) + 1
        f.close()

    with open('/home/pi/logs/errors.json', 'w') as f:
        data[error_name] = error_count
        json.dump(data, f, indent=4, sort_keys=True)
        f.close()
    tweet(json.dumps(data))


def send(data):
    params = ''
    for i in range(len(data)):
        params += '&field' + str(i + 1) + '=' + str(data[i])
    try:
        response = requests.get(update_url + main_api_key + params, timeout=30)
        if response.status_code != 200:
            log_error(requests.exceptions.HTTPError(
                'Request has been failed with status code: {}'.format(
                    response.status_code)))
    except Exception as e:
        log_error(e)


def tweet(message):
    data = json.dumps({'api_key': twitter_api_key, 'status': message})
    try:
        requests.post(tweet_url, data, timeout=30)
    except Exception as e:
        log_error(e)


def get_now():
    d = datetime.now()
    return d.strftime('%Y-%m-%d %H:%M:%S')


def get_month():
    d = datetime.now()
    return d.strftime('%Y_%m')


def get_cpu_temperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return float(res.replace("temp=", "").replace("'C\n", ""))


def get_avg(values, r=0):
    return str(round(sum(values) / float(len(values)), r))


def get_max(values):
    return str(max(values))
