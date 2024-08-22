from src.trading_algo.fetch_data_from_drive import get_option_pattern_parameters
from src.trading_algo.fetch_option_parameters_from_cosmos import cosmosDB_items
from src.trading_algo.fetch_data_from_S3 import Fetch_S3_Files


class option_parameters():
    def fetch_pattern_for_option_selection(self, option_pattern_location):
        if option_pattern_location == 'local':
            import json
            file_path = r"C:\Users\navee\OneDrive\Desktop\Naveen\BhaviAI\algo-trading-system\src\trading_algo\option_selection_pattern.txt"
            with open(file_path, 'r') as file:
                data = json.load(file)
            return data
            
        elif option_pattern_location == 'S3':
            return Fetch_S3_Files().get_option_pattern()
        
        elif option_pattern_location == 'GDrive':
            return get_option_pattern_parameters()
            
        elif option_pattern_location == 'SQL':
            return cosmosDB_items().fetch_option_parameters_from_cosmos()
 
    def update_option_parameter_status(self, option_pattern_location, option_parameter):
        id = option_parameter['id']
        if option_pattern_location == 'SQL':
            cosmosDB_items().update_option_parameters_status(id)
            print("Option marked inactive")

# print(option_parameters().fetch_pattern_for_option_selection('SQL'))