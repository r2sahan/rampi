# 50 23 * * *
import helper


@helper.safe_log
def upload_errors():
    error_files = helper.get_captured_files(helper.LOG_FOLDER + 'error_logs',
                                            'txt')
    helper.upload_files(error_files)
    helper.tweet()


upload_errors()
