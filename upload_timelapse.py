# 0 * * * *
import helper


TIMELAPSE_FOLDER = '/home/pi/timelapse/*/'


@helper.safe_log
def upload_timelapse():
    media_files = helper.get_captured_files(TIMELAPSE_FOLDER, 'avi')
    helper.upload_files(media_files)


upload_timelapse()
