import boto3, os, io, json
import pandas as pd
from io import BytesIO
import pandas as pd

s3 = boto3.client('s3')

class Fetch_S3_Files():
    def __init__(self):
        self.bucket_name = 'algotradifyyearfetching'
        
    def read_spot_data_from_s3(self, file_path):
        try:
            columns = ['<ticker>', '<date>', '<time>', '<open>', '<high>', '<low>', '<close>', '<volume>', '<o/i> ']
            obj = s3.get_object(Bucket=self.bucket_name, Key=file_path)
            data = obj['Body'].read() 
            data_io = BytesIO(data) 
            spot_csv = pd.read_csv(data_io, names=columns, header=None, index_col=False)
            spot_csv.info()
            return spot_csv
        except Exception as e:
            print(f"Error retrieving file from S3: {e}")
            return None
        
    
    def read_historical_option_from_s3(self, file_path):
        try:
            obj = s3.get_object(Bucket=self.bucket_name, Key=file_path)
            data = obj['Body'].read()
            data_io = BytesIO(data)
            historical_option = pd.read_csv(data_io, index_col=False)
            historical_option.info()
            return historical_option
        except Exception as e:
            print(f"Error retrieving file from S3: {e}")
            return None
    
    
    def upload_base_stock_data_with_metrics(self, base_stock_data, csv_filename):
        # Convert the DataFrame to a CSV string
        csv_buffer = io.StringIO()
        base_stock_data.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()

        # Upload the CSV content to S3
        s3_key = f"output/{csv_filename}.csv"
        try:
            # Check if the file already exists
            try:
                s3.head_object(Bucket=self.bucket_name, Key=s3_key)
                # File exists, so delete it first
                s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
                print(f"Existing file '{csv_filename}' in S3 bucket '{self.bucket_name}' replaced")
            except s3.exceptions.ClientError as e:
                # File doesn't exist, continue with upload
                pass

            # Upload the new file
            s3.put_object(Body=csv_content, Bucket=self.bucket_name, Key=s3_key, ACL='bucket-owner-full-control')
            print(f"DataFrame uploaded to S3 bucket '{self.bucket_name}' as '{csv_filename}'")
        except Exception as e:
            print(f"Error uploading DataFrame to S3: {e}")
        
            
    def upload_orderbook(self, base_stock_data, csv_filename): 
        # Download the existing file from S3, if it exists
        s3_key = f"output/{csv_filename}.csv"
        try:
            response = s3.get_object(Bucket=self.bucket_name, Key=s3_key)
            existing_data = pd.read_csv(io.BytesIO(response['Body'].read()))
            # Check if the columns are matching, if not, drop the column names from the DataFrame
            if not existing_data.columns.equals(base_stock_data.columns):
                base_stock_data = base_stock_data.iloc[1:]  # Drop the header row
        except s3.exceptions.NoSuchKey:
            # If the file doesn't exist, create a new DataFrame
            existing_data = pd.DataFrame()

        # Append the new data to the existing DataFrame
        combined_data = pd.concat([existing_data, base_stock_data], ignore_index=True)

        # Convert the combined DataFrame to a CSV string
        csv_buffer = io.StringIO()
        combined_data.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()

        # Upload the updated CSV content to S3
        try:
            s3.put_object(Body=csv_content, Bucket=self.bucket_name, Key=s3_key, ACL='bucket-owner-full-control')
            print(f"DataFrame appended to S3 bucket '{self.bucket_name}' file '{s3_key}'")
        except Exception as e:
            print(f"Error appending DataFrame to S3: {e}")

    def get_option_pattern(self):
        try:
            response = s3.get_object(Bucket = self.bucket_name, Key = 'option_selection_pattern.txt')
            file_content = response['Body'].read().decode('utf-8')
            # Parse the content into a list of dictionaries
            data = json.loads(file_content)
            return data
        except Exception as e:
            print("An error occurred:", e)
            return None

# Example usage
bucket_name = 'algotradifyyearfetching'
file_path_option = '2022/July/BANKNIFTY2271430000PE.csv'
file_path_spot = '2022/Banknifty Spot Data/.NSEBANK.csv'
# fetch = Fetch_S3_Files()
# a = fetch.read_spot_data_from_s3(file_path_spot)
# a = fetch.read_historical_option_from_s3(file_path_option)