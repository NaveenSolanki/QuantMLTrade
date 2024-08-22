import pandas as pd
import os
import datetime

from config import base_directory_project

from src.trading_algo.source import Source
from src.trading_algo.fetch_data_from_drive import upload_order_book
from src.trading_algo.fetch_data_from_S3 import Fetch_S3_Files
from src.trading_algo.fetch_data_from_azure_sql_server import azure_sql_database

class orderbookstorage():
    def __init__(self, output_filename):
        self.output_filename = output_filename
        self.order_book_df = pd.DataFrame(
            columns=['order_id', 'tradingsymbol', 'entry_time', 'exchange', 'transaction_type', 'order_type', 'product',
                     'price', 'trigger_price', 'exit_time', 'entry_price', 'exit_price', 'position', 'trade_status',
                     'comments'])

    def _place_order_historical_data(self, variety, symb, exch, t_type, qty, order_type, product, price, trigger_price,
                                     time_of_trade, comments):
        # check if the symb is in orderbook and trade_status != open
        # if yes create new record in orderbook with this trade and this values trade_status=open, order_id = -1, position=t_type and all the other values
        # if no update the record in orderbook with this trade and this values trade_status=open, tradingsymbol=symb and all the other values
        # place the order

        # create a condition to check if orderbook already contains the symbol and tradestatus is open
        if (len(self.order_book_df[(self.order_book_df['tradingsymbol'] == symb) & (
                self.order_book_df['trade_status'] == 'open')]) > 0) and (list(self.order_book_df[(self.order_book_df[
                                                                                                       'tradingsymbol'] == symb) & (
                                                                                                          self.order_book_df[
                                                                                                              'trade_status'] == 'open')][
                                                                                   'position'])[0] != t_type):
            # update the record in orderbook with this trade and this values trade_status=open, tradingsymbol=symb and all the other values
            self.order_book_df.loc[((self.order_book_df['tradingsymbol'] == symb) & (
                        self.order_book_df['trade_status'] == 'open')), 'exit_price'] = price
            self.order_book_df.loc[((self.order_book_df['tradingsymbol'] == symb) & (
                        self.order_book_df['trade_status'] == 'open')), 'exit_time'] = time_of_trade
            self.order_book_df.loc[((self.order_book_df['tradingsymbol'] == symb) & (
                        self.order_book_df['trade_status'] == 'open')), 'comments'] = comments
            self.order_book_df.loc[((self.order_book_df['tradingsymbol'] == symb) & (
                        self.order_book_df['trade_status'] == 'open')), 'trade_status'] = 'closed'

        else:  # create new record in orderbook with this trade and this values trade_status=open, order_id = -1, position=t_type and all the other values
            # append the record to orderbook
            # self.order_book_df = self.order_book_df.append({'trade_status':'open', 'order_id':-1, 'tradingsymbol':symb,'transaction_type':t_type, 'position':t_type, 'entry_price':price, 'entry_time':time_of_trade}, ignore_index=True)

            self.order_book_df = pd.concat([self.order_book_df, pd.DataFrame([{'trade_status': 'open', 'order_id': -1,
                                                                               'tradingsymbol': symb,
                                                                               'transaction_type': t_type,
                                                                               'position': t_type, 'entry_price': price,
                                                                               'entry_time': time_of_trade,
                                                                               'exit_price': -1,
                                                                               'exit_time': datetime.datetime(2000, 1,
                                                                                                              1, 0, 0,
                                                                                                              0),
                                                                               'comments': ''}])])

        return 0

    def write_orderbook_data_to_disk(self):
        # write the orderbook data to disk in append mode
        # check if below file exists, if not write into it without appending
        #file_path = r'C:\Users\mdevaray\Documents\self\stock_market_project\Git_repos\pykiteconnect_repo\order_book.csv'
        #self.output_filename
        #file_path = r'C:\Users\mdevaray\Documents\self\stock_market_project\Git_repos\pykiteconnect_repo' + "//" + self.output_filename + '.csv'

        if Source == 0:
            file_path = base_directory_project + "\\" + 'output' + "\\" + self.output_filename + '.csv'
            print('orderbook file output ', file_path)
            # check if file exists, if so append else write into it
            if os.path.isfile(file_path):
                self.order_book_df.to_csv(file_path, index=False, mode='a', header=False)
            else:
                self.order_book_df.to_csv(file_path, index=False, mode='w', header=True)
        elif Source == 'GDrive':
            upload_order_book(self.order_book_df)
        elif Source == 'S3':
            Fetch_S3_Files().upload_orderbook(self.order_book_df, self.output_filename)
        elif Source == 'SQL':
            table = 'Orderbook'
            sql = azure_sql_database()
            if sql.check_table_exists(table):
                sql.append_data_to_table(table, self.order_book_df)
            else:
                sql.create_table(table, self.order_book_df)