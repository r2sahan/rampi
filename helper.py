from datetime import datetime, timedelta
import json
import glob
import os
import requests
import subprocess
import sys
from time import sleep
from PIL import Image
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


def log_error(error, func_name):
    with open(LOG_FOLDER + 'error_logs' + get_day() + '.txt', 'a+') as f:
        error_message = '{}: ({}) {}'.format(get_now(), func_name, str(error))
        f.write(error_message + '\n')
        f.close()
        # tweet(error_message)
    count_error(error)


def safe_log(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            log_error(e, func.__name__)
    return wrapper


def log(data):
    with open(LOG_FOLDER + 'sensor_logs_' + get_month() + '.csv', 'a+') as f:
        csv_writer = writer(f)
        csv_writer.writerow([get_now()] + data)
        f.close()


def get_error_json(is_dump=False):
    data = {}
    with open(LOG_FOLDER + 'errors.json', 'r') as f:
        data = json.load(f)
        f.close()
    return json.dumps(data) if is_dump else data


def reset_error_json():
    with open(LOG_FOLDER + 'errors.json', 'w') as f:
        json.dump({}, f, indent=4, sort_keys=True)
        f.close()


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
def paste_image(target_image, filename, y):
    target_image.paste(Image.open(filename), (0, y))


@safe_log
def merge_photos():
    image_files = get_captured_files(PHOTO_FOLDER, 'jpg')
    if not image_files:
        return
    now = get_now2()
    width = 640
    height = 480
    target_image = Image.new('RGB', (width, len(image_files) * height))
    y = 0
    for filename in image_files:
        paste_image(target_image, filename, y)
        os.remove(filename)
        y += height
    target_image.save('{}{}.jpg'.format(PHOTO_FOLDER, now))


@safe_log
def upload_files(captured_files):
    drive = GoogleDrive(credentials_file)
    for filename in captured_files:
        fileid = drive.upload_image(filename)
        drive.share_file_with_me(fileid)
        os.remove(filename)


@safe_log
def upload_error_files():
    error_files = get_captured_files(LOG_FOLDER + 'error_logs', 'txt')
    if error_files:
        upload_files(error_files)
        message = get_error_json(is_dump=True)
        tweet(message)
        reset_error_json()


@safe_log
def delete_old_files():
    chunk_size = 1000  # google drive api limits 1000 queries / 100 seconds
    sleep_time = 100
    days = 10
    drive = GoogleDrive(credentials_file)
    last_day = datetime.now() - timedelta(days=days)
    query = "createdTime < '{}'".format(last_day.strftime('%Y-%m-%d'))
    result = drive.query(query)
    file_ids = list(result.keys())
    if file_ids:
        chunks = [file_ids[x:x + chunk_size]
                  for x in range(0, len(file_ids), chunk_size)]
        for chunk in chunks:
            drive.delete_files(chunk)
            sleep(sleep_time)
        drive.empty_trash()
        tweet('{} files were deleted!'.format(len(file_ids)))


@safe_log
def upload_photos():
    captured_photos = get_captured_files(PHOTO_FOLDER, 'jpg')
    if captured_photos:
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
