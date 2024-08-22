import pyodbc
import pandas as pd

class azure_sql_database:
    def __init__(self):
        # Define Azure SQL Database connection parameters
        self.server = 'algotradifyserver.database.windows.net'
        self.database = 'AlgoTradify'
        self.driver = '{ODBC Driver 18 for SQL Server}'
        self.username = 'sqladmin'
        self.password = 'Algotradify@123'
        self.connection_string = f'DRIVER={self.driver};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password}'
        self.connection = pyodbc.connect(self.connection_string)
        
    def fetch_spot_data_from_azure_sql(self):
        # Establish a connection to the Azure SQL Database
        columns = ['<ticker>', '<date>', '<time>', '<open>', '<high>', '<low>', '<close>', '<volume>', '<o/i> ']

        try:
            query = "SELECT * FROM IndexData"
            # Execute the SQL query and fetch the data into a pandas DataFrame
            data_df = pd.read_sql(query, self.connection)
            # Assign the column names
            data_df.columns = columns
        finally:
            # Close the database connection
            self.connection.close()
        return data_df

    def check_table_exists(self, table_name):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table_name}'")
        return cursor.fetchone()[0] > 0

    def create_table(self, table_name, orderbook):
        cursor = self.connection.cursor()
        # Create table SQL statement
        create_table_sql = f'''
        CREATE TABLE {table_name} (
            order_id INT,
            tradingsymbol NVARCHAR(255),
            entry_time DATETIME,
            exchange FLOAT,
            transaction_type NVARCHAR(255),
            order_type FLOAT,
            product FLOAT,
            price FLOAT,
            trigger_price FLOAT,
            exit_time DATETIME,
            entry_price FLOAT,
            exit_price FLOAT,
            position NVARCHAR(255),
            trade_status NVARCHAR(255),
            comments NVARCHAR(255)
        )
        '''
        # Execute the create table SQL statement
        cursor.execute(create_table_sql)
        self.connection.commit()
        
        # Convert 'entry_time' and 'exit_time' columns to datetime objects
        orderbook['entry_time'] = pd.to_datetime(orderbook['entry_time'])
        orderbook['exit_time'] = pd.to_datetime(orderbook['exit_time'])
        for column in orderbook.columns:
            # Check if the column dtype is float or int
            if orderbook[column].dtype == 'float64' or orderbook[column].dtype == 'int64':
                # Fill missing values with 0 for numeric columns
                orderbook[column] = orderbook[column].fillna(0)
            elif orderbook[column].dtype == 'object':
                # Fill missing values with empty string for object columns
                orderbook[column] = orderbook[column].fillna('')

        # Iterate over DataFrame rows and insert data into the SQL table
        for index, row in orderbook.iterrows():
            insert_sql = f'''
            INSERT INTO {table_name} (order_id, tradingsymbol, entry_time, exchange, transaction_type, order_type, product, price, trigger_price, exit_time, entry_price, exit_price, position, trade_status, comments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(insert_sql, (
                row['order_id'], row['tradingsymbol'], row['entry_time'], row['exchange'], 
                row['transaction_type'], row['order_type'], row['product'], row['price'], 
                row['trigger_price'], row['exit_time'], row['entry_price'], row['exit_price'], 
                row['position'], row['trade_status'], row['comments']
            ))

        # Commit the transaction
        self.connection.commit()        
        self.connection.close()
        print("Orderbook table created successfully!")

    def append_data_to_table(self, table_name, data_df):
        cursor = self.connection.cursor()
        # Convert 'entry_time' and 'exit_time' columns to datetime objects
        data_df['entry_time'] = pd.to_datetime(data_df['entry_time'])
        data_df['exit_time'] = pd.to_datetime(data_df['exit_time'])

        # Fill missing values with appropriate defaults
        data_df = data_df.fillna({'exchange': 0, 'order_type': 0, 'product': 0, 'price': 0, 'trigger_price': 0, 'entry_price': 0, 'exit_price': 0, 'position': '', 'trade_status': '', 'comments': ''})

        # Iterate over DataFrame rows and insert data into the SQL table
        for index, row in data_df.iterrows():
            insert_sql = f'''
            INSERT INTO {table_name} (order_id, tradingsymbol, entry_time, exchange, transaction_type, order_type, product, price, trigger_price, exit_time, entry_price, exit_price, position, trade_status, comments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(insert_sql, (
                row['order_id'], row['tradingsymbol'], row['entry_time'], row['exchange'], 
                row['transaction_type'], row['order_type'], row['product'], row['price'], 
                row['trigger_price'], row['exit_time'], row['entry_price'], row['exit_price'], 
                row['position'], row['trade_status'], row['comments']
            ))

        # Commit the transaction
        self.connection.commit()        
        self.connection.close()
        print("Data appended in the orderbook table!")

# a = fetch_data_from_azure_sql()
# a = azure_sql_database()
# df = pd.read_csv(r"C:\Users\navee\OneDrive\Desktop\Naveen\BhaviAI\Database\Data\sma_trade_orderbook.csv")
# print(df.info())
# if a.check_table_exists('Trades'):
#     a.append_data_to_table('Trades', df)
# else:
#     a.create_table('Trades', df)