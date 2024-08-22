import os
import zipfile
from config import base_directory_project

def extract_files_from_zip(zip_folder_path):
    for root, _, files in os.walk(zip_folder_path):
        for file in files:
            if file.endswith('.zip'):
                zip_file_path = os.path.join(root, file)
                folder_name = os.path.splitext(file)[0]  # Get the name of the zip file without the .zip extension
                #extract_path = os.path.join(root)

                # Create a new folder for extraction if it doesn't exist
                if not os.path.exists(root):
                    os.makedirs(root)

                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(root)
                print(f"Extracted files from {zip_file_path} to {root}")


if __name__ == "__main__":
    base_directory = "."  # Update this to the base directory where the year folders (2011, 2012, ..., 2022) are located.
    #base_directory = r'C:\Users\\Documents\self\stock_market_project\Git_repos\pykiteconnect_repo\drive_data\banknifty'
    #base_directory = r'C:\Users\Mallikarjun\Documents\projects\stock_market\data_sourcing\options_historical_data_aryan_vendor\downloads\banknifty'
    #base_directory = r'C:\Users\Mallikarjun\Documents\projects\stock_market\code\git_repos\algo_trading_system\data\banknifty'

    base_directory = base_directory_project + "\\" + 'data' + '\\' + 'banknifty'

    # Loop through all years from 2011 to 2022
    for year in range(2015, 2023):
        year_directory_path = os.path.join(base_directory, str(year))

        # Check if the year directory exists before extracting
        if os.path.exists(year_directory_path):
            print(f"Extracting files for year {year}")
            extract_files_from_zip(year_directory_path)
        else:
            print(f"Year {year} directory not found. Skipping.")