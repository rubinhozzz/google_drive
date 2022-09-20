from ast import Try
from datetime import datetime
import os.path
from io import BytesIO
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload, MediaIoBaseDownload
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_ID = '0B-OU12dSFJIRNWNhZGNjMDctODUxMi00OWVkLTgzMjAtMTgwMmVlODgzYjBl'
FILE_ID = '1lufg5zqhEipinSDe2MkaFYEmB5NDVZW9beZtwhJER_Q' # 20141028_issues

def _get_service():
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

def _get_mimetype(gd_mimetype):
	return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

def main():
	try:
		service = _get_service()
		if not service:
			raise('No service found.')
		f_metadata = service.files().get(fileId=FILE_ID).execute()
		mimetype = _get_mimetype(f_metadata['mimeType'])
		print(mimetype)
		request = service.files().export_media(fileId=FILE_ID, mimeType=mimetype)
		file = BytesIO()
		downloader = MediaIoBaseDownload(file, request)
		done = False
		while done is False:
			status, done = downloader.next_chunk()
		media = MediaIoBaseUpload(file, mimetype=mimetype)
		service.files().update(fileId=FILE_ID, media_body=media).execute()
		revs = service.revisions().list(fileId=FILE_ID).execute()
		for rev in revs['revisions']:
			print(rev['id'])
	except Exception as ex:
		print(ex)
	

if __name__ == '__main__':
	main()