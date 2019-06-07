import datetime
import logging
import os
import httplib2
# Required oauth2client==3.0.0
from apiclient import discovery
from apiclient import errors
from apiclient.http import MediaFileUpload


class DriveError(Exception):
    pass


class GoogleDrive:
    """
    Handling the Google Drive Access
    """

    SCOPES = ['https://www.googleapis.com/auth/drive']
    FOLDER_MIME = 'application/vnd.google-apps.folder'
    EMAIL = 'rampi.harman@gmail.com'

    def __init__(self, secret):
        if not os.path.exists(secret):
            raise DriveError("Secret file does not exists")
        self.client_secret_file = secret
        self.logger = logging.getLogger('GoogleDriveUploader')
        self.service = self.authorize()

    def authorize(self):
        """Gets valid user credentials from storage.
        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.
        """
        from oauth2client.service_account import ServiceAccountCredentials
        scopes = self.SCOPES
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            self.client_secret_file, scopes=scopes)
        http = credentials.authorize(httplib2.Http())
        return discovery.build('drive', 'v3', http=http)

    def upload_image(self, filename, parents=None):
        """
        Upload image file
        :param filename: ...
        """
        media_body = MediaFileUpload(filename, mimetype='image/jpeg',
                                     resumable=True)
        if parents and isinstance(parents, str):
            parents = [parents]
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        body = {
            'name': os.path.basename(filename),
            'description': now,
            'parents': parents
        }

        try:
            upload = self.service.files().create(
                body=body, media_body=media_body).execute()
            self.logger.info("Uploaded image to Drive (Id: %s)", upload['id'])
            return upload['id']
        except errors.HttpError as error:
            self.logger.error("Could not upload image %s", error)
            return None

    def create_folder(self, name, parents=None):
        """
        :param name:
        :param kwargs: Anything that create(body=kwargs) accepts
        """
        body = {
            'mimeType': self.FOLDER_MIME,
            'name': name,
        }
        if parents:
            body['parents'] = [parents]
        fid = self.service.files().create(body=body).execute()
        return fid

    def share_folder_with_users(self, fileid, emails):
        """
        Share the folder or file with a specific user.
        :param fileid: id of the object we want to share, can be file or folder
        :param emails: list of email addresses of the user to share the folder
        """
        for email in emails:
            if not self.share_folder_with_user(fileid, email):
                return False
        return True

    def share_folder_with_user(self, fileid, email):
        """
        Share the folder or file with a specific user.
        :param fileid: id of the object we want to share, can be file or folder
        :param email: email address of the user to share the folder with.
        """
        body = {
            'role': 'writer',
            'type': 'user',
            'emailAddress': email
        }
        self.logger.debug("Creating permission for id %s", fileid)
        try:
            self.service.permissions().create(
                fileId=fileid, body=body,
                sendNotificationEmail=False).execute()
        except errors.HttpError as error:
            self.logger.error("Unable to set permissions %s", error)
            return False
        else:
            return True

    def share_file_with_me(self, fileid):
        return self.share_folder_with_user(fileid, self.EMAIL)

    def delete_file(self, fileid):
        """Delete a file using Files.Delete()
        (WARNING: deleting permanently deletes the file!)
        :param param: additional parameter to file.
        :type param: dict.
        :raises: ApiRequestError
        """
        try:
            self.service.files().delete(fileId=fileid).execute()
        except errors.HttpError as error:
            self.logger.error("Could not delete image %s", error)
            return False
        else:
            return True

    def search_files(self, mime_type=None):
        """
        Search files with given query, return name and id
        :returns: dict with keys name and id
        """
        if not mime_type:
            mime_type = "image/jpeg"

        query = "mimeType='%s'" % mime_type
        return self.query(query)

    def query(self, query):
        """
        :returns: dict with the id, name pair of the result
        """
        result = {}
        page_token = None
        while True:
            response = self.service.files().list(
                q=query, spaces='drive',
                fields='nextPageToken, files(id, name)',
                pageToken=page_token).execute()
            for file in response.get('files', []):
                result[file.get('id')] = file.get('name')
                self.logger.info('Found file: %s (%s)', file.get('name'),
                                 file.get('id'))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        return result
