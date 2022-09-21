import sys
from datetime import datetime
import os.path
from io import BytesIO
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload, MediaIoBaseDownload
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/drive']
FILE_ID = '1lufg5zqhEipinSDe2MkaFYEmB5NDVZW9beZtwhJER_Q' # 20141028_issues
MIME_TYPES = {
	'application/vnd.google-apps.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
	'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
	'application/vnd.google-apps.presentation': 'application/vnd.ms-powerpoint'
}

service = None

def _get_service():
	if service:
		return service
	creds = None
	# The file token.json stores the user's access and refresh tokens, and is
	# created automatically when the authorization flow completes for the first
	# time.
	if os.path.exists('token.json'):
		creds = Credentials.from_authorized_user_file('token.json', SCOPES)
	if not creds or not creds.valid:
	# If there are no (valid) credentials available, let the user log in.
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
			creds = flow.run_local_server(port=0)
		# Save the credentials for the next run
		with open('token.json', 'w') as token:
			token.write(creds.to_json())
	return build('drive', 'v3', credentials=creds)

def _get_mimetype(gd_mimetype: str) -> str:
	print('GD MIMETYPE: ', gd_mimetype)
	if gd_mimetype in MIME_TYPES:
		return MIME_TYPES[gd_mimetype] 
	return ''

def _get_last_revision(file_id: str) -> int:
	service = _get_service()
	response = service.revisions().list(fileId=FILE_ID).execute()
	if not response:
		return None
	revs = response['revisions']
	return revs[-1]['id']

def main(file_id: str):
	try:
		service = _get_service()
		if not service:
			raise('No service found.')
		f_metadata = service.files().get(fileId=file_id).execute()
		mimetype = _get_mimetype(f_metadata['mimeType'])
		print(mimetype)
		if not mimetype:
			raise('Mimetype not found.')
		request = service.files().export_media(fileId=file_id, mimeType=mimetype)
		file = BytesIO()
		downloader = MediaIoBaseDownload(file, request)
		done = False
		while done is False:
			status, done = downloader.next_chunk()
		media = MediaIoBaseUpload(file, mimetype=mimetype)
		service.files().update(fileId=file_id, media_body=media).execute()
		rev_no = _get_last_revision(file_id)
		if not rev_no:
			raise('No revision created.')
		print('New revision created: {}.'.format(rev_no))
	except Exception as ex:
		print(ex)
	
if __name__ == '__main__':
	file_id = FILE_ID
	if len(sys.argv) > 1:
		file_id = sys.argv[1]
		print('File id received: {}.'.format(file_id))
	else:
		print('Getting default file with id {}.'.format(FILE_ID))
	main(file_id)