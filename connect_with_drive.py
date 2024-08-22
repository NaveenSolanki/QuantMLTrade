from __future__ import print_function

import os.path

import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']


def Gdrive():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)

        # Call the Drive v3 API
        results = service.files().list(
             fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
            return
        # print('Files:')
        for item in items:
            # print(u'{0} ({1})'.format(item['name'], item['id']))
            if item['name'] == 'heart.csv':
                # Access the content of the file using its ID
                file_id = item['id']
                request = service.files().get_media(fileId=file_id)
                content = request.execute()

                # Read the CSV content into a pandas DataFrame
                from io import StringIO

                csv_content = content.decode('utf-8')  # Assuming the file is in UTF-8 encoding
                df = pd.read_csv(StringIO(csv_content))
                print(df.head())

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    Gdrive()