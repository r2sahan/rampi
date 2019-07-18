# 50 23 * * *
import helper


@helper.safe_log
def upload_errors():
    error_files = helper.get_captured_files(helper.LOG_FOLDER + 'error_logs',
                                            'txt')
    helper.upload_files(error_files)
    message = helper.get_error_json(is_dump=True)
    helper.tweet(message)


upload_errors()
