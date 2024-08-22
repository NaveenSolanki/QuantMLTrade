import io, json
import pandas as pd
import googleapiclient
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload, MediaIoBaseDownload
from googleapiclient.http import MediaInMemoryUpload
from config import base_directory_project

# Authenticate using OAuth 2.0 credentials
SCOPES = ['https://www.googleapis.com/auth/drive']
token_json = base_directory_project + "/token.json"
creds = Credentials.from_authorized_user_file(token_json, SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

def read_spot_data_csv_file_from_drive(column):
    parent_folder_name = '2022'
    folder_name = 'Banknifty Spot Data'
    file_name = '.NSEBANK.csv'
    # Search for the parent folder
    parent_folder_query = f"name='{parent_folder_name}' and mimeType='application/vnd.google-apps.folder'"
    parent_folder_results = drive_service.files().list(q=parent_folder_query).execute()
    parent_folder_id = parent_folder_results.get('files', [])[0]['id'] if parent_folder_results.get('files', []) else None

    if parent_folder_id:
        # Search for the folder within the parent folder
        folder_query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_folder_id}' in parents"
        folder_results = drive_service.files().list(q=folder_query).execute()
        folder_id = folder_results.get('files', [])[0]['id'] if folder_results.get('files', []) else None

        if folder_id:
            # Search for the specific file within the folder
            file_query = f"name='{file_name}' and '{folder_id}' in parents"
            file_results = drive_service.files().list(q=file_query).execute()
            file_id = file_results.get('files', [])[0]['id'] if file_results.get('files', []) else None

            if file_id:
                # Fetch the content of the file
                file_data = drive_service.files().get_media(fileId=file_id)
                file_stream = io.BytesIO()
                downloader = googleapiclient.http.MediaIoBaseDownload(file_stream, file_data)
                done = False
                while not done:
                    status, done = downloader.next_chunk()

                # You can now process the file_stream as needed

                file_stream.seek(0)
                df = pd.read_csv(file_stream, encoding='utf-8', header=None, delimiter=',', names=column)
                return df
            else:
                print(f"File '{file_name}' not found within '{folder_name}'.")
                return None
        else:
            print(f"Folder '{folder_name}' not found within '{parent_folder_name}'.")
    else:
        print(f"Parent folder '{parent_folder_name}' not found.")

def read_historical_option_data_csv_file_from_drive(instrument, month_name_to_fetch):
    parent_folder_name = '2022'
    folder_name = month_name_to_fetch
    file_name = instrument + '.csv'
    # Search for the parent folder
    parent_folder_query = f"name='{parent_folder_name}' and mimeType='application/vnd.google-apps.folder'"
    parent_folder_results = drive_service.files().list(q=parent_folder_query).execute()
    parent_folder_id = parent_folder_results.get('files', [])[0]['id'] if parent_folder_results.get('files',
                                                                                                    []) else None

    if parent_folder_id:
        # Search for the folder within the parent folder
        folder_query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_folder_id}' in parents"
        folder_results = drive_service.files().list(q=folder_query).execute()
        folder_id = folder_results.get('files', [])[0]['id'] if folder_results.get('files', []) else None

        if folder_id:
            # Search for the specific file within the folder
            file_query = f"name='{file_name}' and '{folder_id}' in parents"
            file_results = drive_service.files().list(q=file_query).execute()
            file_id = file_results.get('files', [])[0]['id'] if file_results.get('files', []) else None

            if file_id:
                # Fetch the content of the file
                file_data = drive_service.files().get_media(fileId=file_id)
                file_stream = io.BytesIO()
                downloader = googleapiclient.http.MediaIoBaseDownload(file_stream, file_data)
                done = False
                while not done:
                    status, done = downloader.next_chunk()

                # You can now process the file_stream as needed

                file_stream.seek(0)
                df = pd.read_csv(file_stream, encoding='utf-8')
                return df
            else:
                print(f"File '{file_name}' not found within '{folder_name}'.")
                return None
        else:
            print(f"Folder '{folder_name}' not found within '{parent_folder_name}'.")
    else:
        print(f"Parent folder '{parent_folder_name}' not found.")

def upload_base_stock_data_with_metrics(base_stock_data):

    # Assuming you have a DataFrame named 'base_stock_data' that you want to upload
    csv_data = base_stock_data.to_csv(index=False)
    csv_data_bytes = csv_data.encode('utf-8')  # Encode the CSV data as bytes

    # Specify the folder name you want to create/upload to
    folder_name = "output_data"
    csv_filename = 'base_stock_data_with_metrics.csv'

    # Check if the folder already exists
    folder_exists = False
    results = drive_service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id)").execute()
    files = results.get('files', [])

    if files:
        # The folder already exists; retrieve its ID
        folder_id = files[0]['id']
        folder_exists = True

    # Create the folder if it doesn't exist
    if not folder_exists:
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
        folder_id = folder.get('id')

    # Check if the file already exists in the folder
    file_exists = False
    results = drive_service.files().list(q=f"name='{csv_filename}' and '{folder_id}' in parents and trashed=false",
                                         fields="files(id)").execute()
    files = results.get('files', [])

    if files:
        # The file already exists; retrieve its ID
        file_id = files[0]['id']
        file_exists = True

    # Upload the CSV data as a new file or update the existing file
    file_metadata = {
        'name': csv_filename,
        'parents': [folder_id]
    }

    media = MediaInMemoryUpload(csv_data_bytes, mimetype='text/csv')

    if file_exists:
        # Update the existing file
        drive_service.files().update(fileId=file_id, media_body=media).execute()
        print(f"'{csv_filename}' has been updated in the '{folder_name}' folder.")
    else:
        # Create a new file
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"DataFrame has been uploaded as '{csv_filename}' to the '{folder_name}' folder.")


def upload_order_book(order_book_df):
    csv_data = order_book_df.to_csv(index=False)
    csv_data_bytes = csv_data.encode('utf-8')  # Encode the CSV data as bytes

    # Specify the folder name you want to create/upload to
    folder_name = "output_data"
    csv_filename = 'sma_trade_orderbook.csv'

    # Check if the folder already exists
    folder_exists = False
    results = drive_service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id)").execute()
    files = results.get('files', [])

    if files:
        # The folder already exists; retrieve its ID
        folder_id = files[0]['id']
        folder_exists = True

    # Create the folder if it doesn't exist
    if not folder_exists:
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
        folder_id = folder.get('id')

    # Check if the file already exists in the folder
    file_exists = False
    results = drive_service.files().list(
        q=f"name='{csv_filename}' and '{folder_id}' in parents and trashed=false",
        fields="files(id)").execute()
    files = results.get('files', [])

    if files:
        # The file already exists; retrieve its ID
        file_id = files[0]['id']
        file_exists = True

    # Retrieve the existing file's content
    existing_content = ''
    if file_exists:
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        existing_content = fh.getvalue().decode('utf-8')

    # Check if we should include column names
    include_column_names = not file_exists

    # Append the new data to the content, optionally including column names
    if include_column_names:
        updated_content = csv_data
    else:
        updated_content = csv_data.split('\n', 1)[-1]  # Remove the first line (column names) from the new data

    if existing_content:
        # Remove any empty lines from the existing content
        existing_content_lines = existing_content.split('\n')
        existing_content = '\n'.join(line for line in existing_content_lines if line.strip())

        if existing_content:
            updated_content = existing_content + '\n' + updated_content

    # Upload the updated content to the file
    media = MediaIoBaseUpload(io.BytesIO(updated_content.encode('utf-8')), mimetype='text/csv', resumable=True)

    if file_exists:
        # Update the existing file's content
        drive_service.files().update(fileId=file_id, media_body=media).execute()
        print(f"'{csv_filename}' has been updated in the '{folder_name}' folder.")
    else:
        # Create a new file with the updated content
        file_metadata = {
            'name': csv_filename,
            'parents': [folder_id]
        }
        drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"DataFrame has been uploaded as '{csv_filename}' to the '{folder_name}' folder.")

def upload_order_book_replace(order_book_df):
    csv_data = order_book_df.to_csv(index=False)
    csv_data_bytes = csv_data.encode('utf-8')  # Encode the CSV data as bytes

    # Specify the folder name you want to replace the file in
    folder_name = "output_data"
    csv_filename = 'sma_trade_orderbook.csv'

    # Check if the folder already exists
    folder_exists = False
    results = drive_service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id)").execute()
    files = results.get('files', [])

    if files:
        # The folder already exists; retrieve its ID
        folder_id = files[0]['id']
        folder_exists = True

    # Create the folder if it doesn't exist
    if not folder_exists:
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
        folder_id = folder.get('id')

    # Check if the file already exists in the folder
    file_exists = False
    results = drive_service.files().list(
        q=f"name='{csv_filename}' and '{folder_id}' in parents and trashed=false",
        fields="files(id)").execute()
    files = results.get('files', [])

    if files:
        # The file already exists; retrieve its ID
        file_id = files[0]['id']
        file_exists = True

    # Upload the new content to the file, replacing the existing content
    media = MediaIoBaseUpload(io.BytesIO(csv_data_bytes), mimetype='text/csv', resumable=True)

    if file_exists:
        # Update the existing file's content
        drive_service.files().update(fileId=file_id, media_body=media).execute()
        print(f"'{csv_filename}' has been replaced in the '{folder_name}' folder.")
    else:
        # Create a new file with the new content
        file_metadata = {
            'name': csv_filename,
            'parents': [folder_id]
        }
        drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"DataFrame has been uploaded as '{csv_filename}' to the '{folder_name}' folder.")

def get_option_pattern_parameters():
    # Search for the folder within the parent folder
    folder_name = 'data-file-system'
    file_name = 'option_selection_patten.txt'
    folder_query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    folder_results = drive_service.files().list(q=folder_query).execute()
    folder_id = folder_results.get('files', [])[0]['id'] if folder_results.get('files', []) else None

    if folder_id:
        # Search for the specific file within the folder
        file_query = f"name='{file_name}' and '{folder_id}' in parents"
        file_results = drive_service.files().list(q=file_query).execute()
        file_id = file_results.get('files', [])[0]['id'] if file_results.get('files', []) else None
        if file_id:
            # Fetch the content of the file
            request = drive_service.files().get_media(fileId=file_id)
            file_stream = io.BytesIO()
            downloader = MediaIoBaseDownload(file_stream, request)

            # Download the file content
            done = False
            while not done:
                status, done = downloader.next_chunk()

            # Reset the file stream cursor to the beginning
            file_stream.seek(0)
            
            # Read the content of the file
            file_content = file_stream.getvalue().decode('utf-8')
             # Parse the content into a list of dictionaries
            data = json.loads(file_content)

            return data
        else:
            print(f"File '{file_name}' not found within '{folder_name}'.")
            return None
    else:
        print(f"Folder '{folder_name}' not found.")
    
    
# data = get_option_pattern_parameters()
# print(data)
# print(type(data))
# temp = [{'type': 'CE', 'sel_criteria': 'strike_price', 'itm_atm_otm': 'otm', 'delta_strike_price': -300, 'option_name': '', 'execution_strategy': {'simple_selling': {'short_action': 'SELL'}}},
#                                         {'type': 'PE', 'sel_criteria': 'strike_price', 'itm_atm_otm': 'otm','delta_strike_price': -300, 'option_name': '', 'execution_strategy': {'simple_selling': {'long_action': 'SELL'}}}]
# print(type(temp))
# columns = ['<ticker>','<date>','<time>','<open>','<high>','<low>','<close>','<volume>','<o/i> ']
# print(read_historical_option_data_csv_file_from_drive('BANKNIFTY2271430000PE', 'July').head())
# print(read_spot_data_csv_file_from_drive(columns).head())
# upload_order_book(pd.DataFrame())