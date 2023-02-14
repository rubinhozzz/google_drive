import os
from io import BytesIO
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.shortcuts import redirect
SCOPES = [
	'https://www.googleapis.com/auth/drive.metadata.readonly',
	'https://www.googleapis.com/auth/drive',
	'https://www.googleapis.com/auth/drive.metadata',
	'https://www.googleapis.com/auth/drive.file']
DRIVE_ID = '0AEUBgtW_o-MoUk9PVA'
CLIENT_SECRETS_FILE = os.path.join(settings.GD_CREDENTIALS_DIR, 'credentials.json')
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

class GDClient():

	def __init__(self, username=None, request=None) -> None:
		if not username:
			raise Exception('username is mandatory in order to create this object.')
		self.username = username
		self.request = request

	def get_service(self):
		if 'credentials' not in self.request.session:
			return None
		# Load credentials from the session.
		credentials = Credentials(**self.request.session['credentials'])
		return build('drive', 'v3', credentials=credentials)

	def create_folder(self, parent_folder_id, name):
		try:
			service = self.get_service()
			response = service.files().list(q="name='{}' and mimeType = 'application/vnd.google-apps.folder' and '{}' in parents and trashed=false".format(name, parent_folder_id),
										fields='files(id, name)',
										includeItemsFromAllDrives=True,
										supportsAllDrives=True).execute()
			files = response.get('files', [])
			if files:
				return files[0].get('id')
			folder_metadata = {
				'name' : name,
				'mimeType' : 'application/vnd.google-apps.folder',
				'parents': [parent_folder_id]
			}
			folder = service.files().create(body=folder_metadata, fields='id', supportsAllDrives=True).execute()
			return folder.get('id')
		except HttpError as error:
			print(error)
			return None

def authorize(request):
	flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
	flow.redirect_uri = 'http://localhost:8080/oauth2callback'
	authorization_url, state = flow.authorization_url(
		access_type='offline',
		include_granted_scopes='true')
	request.session['state'] = state
	return redirect(authorization_url)

def oauth2callback(request):
	state = request.session['state']

	flow = Flow.from_client_secrets_file(
		CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
	flow.redirect_uri = 'http://localhost:8080/oauth2callback'

	authorization_response = request.build_absolute_uri()
	flow.fetch_token(authorization_response=authorization_response)

	credentials = flow.credentials
	request.session['credentials'] = credentials_to_dict(credentials)
	return redirect('dashboard')

def credentials_to_dict(credentials):
	return {'token': credentials.token,
			'refresh_token': credentials.refresh_token,
			'token_uri': credentials.token_uri,
			'client_id': credentials.client_id,
			'client_secret': credentials.client_secret,
			'scopes': credentials.scopes}

