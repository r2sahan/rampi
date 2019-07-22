from datetime import datetime
import json
import glob
import os
import requests
import subprocess
import sys
from time import sleep
# from _thread import start_new_thread
from csv import writer
from googledrive import GoogleDrive

if sys.version_info[0] == 2:
    import ConfigParser as configparser
else:
    import configparser


config = configparser.ConfigParser()
config.read('/home/pi/private/config.ini')


main_api_key = config['DEFAULT']['MAIN_API_KEY']
twitter_api_key = config['DEFAULT']['TWITTER_API_KEY']
credentials_file = config['DEFAULT']['CREDENTIALS_FILE']

update_url = 'https://api.thingspeak.com/update?api_key='
tweet_url = 'https://api.thingspeak.com/apps/thingtweet/1/statuses/update'

LOG_FOLDER = '/home/pi/logs/'
PHOTO_FOLDER = '/home/pi/captured/'
TIMELAPSE_FOLDER = '/home/pi/timelapse/'


def log(data):
    with open(LOG_FOLDER + 'sensor_logs_' + get_month() + '.csv', 'a+') as f:
        csv_writer = writer(f)
        csv_writer.writerow([get_now()] + data)
        f.close()


def log_error(error, func_name):
    with open(LOG_FOLDER + 'error_logs' + get_day() + '.txt', 'a+') as f:
        f.write('{}: ({}) {}\n'.format(get_now(), func_name, str(error)))
        f.close()
    count_error(error)


def safe_log(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            log_error(e, func.__name__)
    return wrapper


def get_error_json(is_dump=False):
    data = {}
    with open(LOG_FOLDER + 'errors.json', 'r') as f:
        data = json.load(f)
        f.close()
    return json.dumps(data) if is_dump else data


def count_error(error):
    error_count = 0
    error_name = type(error).__name__
    data = get_error_json()
    error_count = data.get(error_name, 0) + 1
    data[error_name] = error_count
    with open(LOG_FOLDER + 'errors.json', 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)
        f.close()


@safe_log
def send(data):
    params = ''
    for i in range(len(data)):
        params += '&field' + str(i + 1) + '=' + str(data[i])
    response = requests.get(update_url + main_api_key + params, timeout=30)
    if response.status_code != 200:
        raise requests.exceptions.HTTPError(
            'Request has been failed with status code: {}'.format(
                response.status_code))


@safe_log
def tweet(message):
    data = {'api_key': twitter_api_key, 'status': message}
    requests.post(tweet_url, data, timeout=30)


def get_now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_now2():
    return datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


def get_month():
    return datetime.now().strftime('%Y_%m')


def get_day():
    return datetime.now().strftime('%Y_%m_%d')


def get_cpu_temperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return float(res.replace("temp=", "").replace("'C\n", ""))


def get_avg(values, r=0):
    return str(round(sum(values) / float(len(values)), r))


def get_max(values):
    return str(max(values))


def get_sum(values):
    return str(sum(values))


def get_captured_files(folder, extension):
    return sorted(glob.glob('{}*.{}'.format(folder, extension)))


@safe_log
def merge_photos():
    # pip install Pillow
    from PIL import Image
    image_files = get_captured_files(PHOTO_FOLDER, 'jpg')
    now = get_now2()
    width = 640
    height = 480
    merge_image = Image.new('RGB', (width, len(image_files) * height))
    y = 0
    for filename in image_files:
        merge_image.paste(Image.open(filename), (0, y))
        os.remove(filename)
        y += height
    merge_image.save('{}{}.jpg'.format(PHOTO_FOLDER, now))


def upload_files(captured_files):
    drive = GoogleDrive(credentials_file)
    for filename in captured_files:
        fileid = drive.upload_image(filename)
        drive.share_file_with_me(fileid)
        os.remove(filename)


def upload_photos():
    captured_photos = get_captured_files(PHOTO_FOLDER, 'jpg')
    upload_files(captured_photos)


@safe_log
def capture_photos():
    cmd = 'fswebcam -d /dev/video{} -r 640x480 -S 2 --no-banner --no-info ' \
        '--no-timestamp {}{}-{}.jpg'
    now = get_now2()
    subprocess.Popen(cmd.format('0', PHOTO_FOLDER, now, 'out').split())
    sleep(0.5)
    subprocess.Popen(cmd.format('1', PHOTO_FOLDER, now, 'in').split())


def capture(motions):
    if is_real_motion(motions):
        capture_photos()
        sleep(4.5)
        merge_photos()
        sleep(0.5)
        upload_photos()


def is_real_motion(motions):
    return sum(motions) > 0
