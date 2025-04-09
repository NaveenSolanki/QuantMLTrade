import pandas as pd
import requests
import os
import datetime

from config import base_directory_project
from src.trading_algo import fetch_data_from_drive
from src.trading_algo.fetch_data_from_S3 import Fetch_S3_Files
from src.trading_algo.source import Source
from src.trading_algo.fetch_data_from_azure_sql_server import azure_sql_database

base_folder_for_hist_data = base_directory_project + "/" + 'data'



class RangeDataInterfaceLiveAndHistorical():
    def __init__(self, live_data_fetch_flag=0):
        self.live_data_fetch_flag = live_data_fetch_flag
        self.spot_data_df = None
        self.cur_spot_data_df = None
        self._option_ce_data = None
        self._option_pe_data = None
        self._base_stock = 'BANKNIFTY'
        self.option_data_df = None
        self.cur_option_data_df = None

        self.option_name = {'BANKNIFTY': '.NSEBANK', 'NIFTY': '.nifty'}

    # if self._base_stock == 'BANKNIFTY':
    # 	self.option_name = '.NSEBANK'
    # elif self._base_stock == 'NIFTY':
    # 	self.option_name = '.nifty'

    # instrument can contain these values ['NIFTY', 'BANKNIFTY']

    def get_ltp_spot(self, instrument, start_time, end_time):

        if self.live_data_fetch_flag == 1:
            if instrument == "BANKNIFTY":
                spot_name_updated_for_live = "NSE:" + "NIFTY BANK"
            elif instrument == "NIFTY":
                spot_name_updated_for_live = "NSE:" + instrument + " 50"
            else:
                spot_name_updated_for_live = ''
            return self.get_live_ltp_spot(spot_name_updated_for_live, datetime_to_fetch)
        else:
            return self.get_historical_spot(instrument, start_time, end_time)

    def get_ltp_option(self, instrument, start_time, end_time):
        if self.live_data_fetch_flag == 1:
            option_name_updated_for_live = "NFO:" + instrument
            return self.get_live_ltp_option(option_name_updated_for_live, datetime_to_fetch)
        else:
            return self.get_historical_option(instrument, start_time, end_time)

    def get_live_ltp_spot(self, instrument, datetime_to_fetch):
        url = "http://localhost:4000/ltp?instrument=" + instrument
        try:
            resp = requests.get(url)
        except Exception as e:
            print(e)
        data = resp.json()
        return data

    def read_spot_data(self, instrument, datetime_to_fetch):
        date_to_fetch = datetime_to_fetch.strftime("%Y-%m-%d")
        # create only time from datetime_to_fetch
        time_to_fetch = datetime_to_fetch.strftime("%H:%M:%S")
        # get year from date
        year_to_fetch = datetime_to_fetch.strftime("%Y")
        # get month from	date
        month_to_fetch = datetime_to_fetch.strftime("%m")
        # get name of the month from above month date
        month_name_to_fetch = datetime_to_fetch.strftime("%B")
        yearmo_to_fetch = year_to_fetch + '_' + month_to_fetch

        path_to_fetch_spot_data = None
        year_to_fetch = datetime_to_fetch.strftime("%Y")
        # create this path: base_path/year/bank_nifty/.nsebkank.csv
        if Source == 0:
            path_to_fetch_spot_data = os.path.join(base_folder_for_hist_data, 'banknifty', year_to_fetch,
                                                   'Banknifty Spot Data', '.NSEBANK.csv')

        columns = ['<ticker>', '<date>', '<time>', '<open>', '<high>', '<low>', '<close>', '<volume>', '<o/i> ']
        # read spot datafrom without header and assign above column names

        # check if self.spot_data_df is None or len=0 then read the csv file
        if (self.spot_data_df is None) or (len(self.spot_data_df) == 0):
            print('reading spot none')
            if Source == 0:
                self.cur_spot_data_df = pd.read_csv(path_to_fetch_spot_data, header=None, names=columns)
            elif Source == 'GDrive':
                self.cur_spot_data_df = fetch_data_from_drive.read_spot_data_csv_file_from_drive(columns)
            elif Source == 'S3':
                file_path = f'{year_to_fetch}/Banknifty Spot Data/.NSEBANK.csv'
                self.cur_spot_data_df = Fetch_S3_Files().read_spot_data_from_s3(file_path)
            elif Source == 'SQL':
                self.cur_spot_data_df = azure_sql_database().fetch_spot_data_from_azure_sql()
            # convert date column to date datatype and get only date with format %y-%m-%d
            self.cur_spot_data_df['<date>'] = pd.to_datetime(self.cur_spot_data_df['<date>'], format='%d-%m-%Y').dt.date
            self.cur_spot_data_df['month_of_date'] = self.cur_spot_data_df['<date>'].apply(lambda x: x.strftime('%m'))
            self.cur_spot_data_df['year_of_date'] = self.cur_spot_data_df['<date>'].apply(lambda x: x.strftime('%Y'))
            self.cur_spot_data_df['yearmo'] = self.cur_spot_data_df['year_of_date'] + '_' + self.cur_spot_data_df[
                'month_of_date']
            # convert the date to this format '%y-%m-%d'
            self.cur_spot_data_df['<date>'] = self.cur_spot_data_df['<date>'].apply(lambda x: x.strftime('%Y-%m-%d'))

            # convert time column to time
            if Source != 'SQL':
                self.cur_spot_data_df['<time>'] = pd.to_datetime(self.cur_spot_data_df['<time>'], format='mixed').dt.time
            # convert time to this string time format '%H:%M:%S'
            self.cur_spot_data_df['<time>'] = self.cur_spot_data_df['<time>'].apply(lambda x: x.strftime('%H:%M:%S'))
            # write elseif condition to check if instrument is equal to ticker and datetime_to_fetch is present in dataframe date
            # append cur_spot_data_df to self.spot_data_df using concat
            # create a datetime column which is a combination of date and time and convert into datetime object
            self.cur_spot_data_df['datetime'] = pd.to_datetime(
                self.cur_spot_data_df['<date>'] + ' ' + self.cur_spot_data_df['<time>'])
            self.spot_data_df = pd.concat([self.spot_data_df, self.cur_spot_data_df], ignore_index=True)
            print('shape after appending', self.spot_data_df.shape)

        # elif  self.option_name[instrument] == self.spot_data_df['<ticker>'][0] and datetime_to_fetch.strftime("%Y-%m-%d") in self.spot_data_df['<date>'].values:
        elif (self.option_name[instrument] in list(pd.unique(self.spot_data_df['<ticker>']))) and (
                str(yearmo_to_fetch) in list(pd.unique(self.spot_data_df['yearmo']))):
            # elif  self.option_name[instrument] in list(pd.unique(self.spot_data_df['<ticker>'])) and datetime_to_fetch.strftime("%Y-%m-%d") in self.spot_data_df['<date>'].values:
            print('no need to read spot')
        else:
            print('reading spot not found')
            print('yearmo value ', yearmo_to_fetch)
            print('list of yearmo ', list(pd.unique(self.spot_data_df['yearmo'])))
            if str(yearmo_to_fetch) in list(pd.unique(self.spot_data_df['yearmo'])):
                print('working')
            else:
                print('not working')

            # .NSEBANK
            if Source == 0:
                self.cur_spot_data_df = pd.read_csv(path_to_fetch_spot_data, header=None, names=columns)
            elif Source == 'GDrive':
                self.cur_spot_data_df = fetch_data_from_drive.read_spot_data_csv_file_from_drive(columns, year_to_fetch)
            elif Source == 'S3':
                file_path = f'{year_to_fetch}/Banknifty Spot Data/.NSEBANK.csv'
                self.cur_spot_data_df = Fetch_S3_Files().read_spot_data_from_s3(file_path)
            elif Source == 'SQL':
                self.cur_spot_data_df = azure_sql_database().fetch_spot_data_from_azure_sql()
            # convert date column to date datatype and get only date with format %y-%m-%d
            self.cur_spot_data_df['<date>'] = pd.to_datetime(self.cur_spot_data_df['<date>'], format='%d-%m-%Y').dt.date
            self.cur_spot_data_df['month_of_date'] = self.cur_spot_data_df['<date>'].apply(lambda x: x.strftime('%m'))
            self.cur_spot_data_df['year_of_date'] = self.cur_spot_data_df['<date>'].apply(lambda x: x.strftime('%Y'))
            self.cur_spot_data_df['yearmo'] = self.cur_spot_data_df['year_of_date'] + '_' + self.cur_spot_data_df[
                'month_of_date']
            # convert the date to this format '%y-%m-%d'
            self.cur_spot_data_df['<date>'] = self.cur_spot_data_df['<date>'].apply(lambda x: x.strftime('%Y-%m-%d'))
            # convert time column to time
            if Source != 'SQL':
                self.cur_spot_data_df['<time>'] = pd.to_datetime(self.cur_spot_data_df['<time>'], format='mixed').dt.time
            # convert time to this string time format '%H:%M:%S'
            self.cur_spot_data_df['<time>'] = self.cur_spot_data_df['<time>'].apply(lambda x: x.strftime('%H:%M:%S'))
            # write elseif condition to check if instrument is equal to ticker and datetime_to_fetch is present in dataframe date
            self.cur_spot_data_df['datetime'] = pd.to_datetime(
                self.cur_spot_data_df['<date>'] + ' ' + self.cur_spot_data_df['<time>'])
            self.spot_data_df = pd.concat([self.spot_data_df, self.cur_spot_data_df], ignore_index=True)
            print('shape after appending', self.spot_data_df.shape)

        return 0

    def get_historical_spot(self, instrument, start_date,
                            end_date):  # consider we will at max need to fetch last month of data

        self.read_spot_data(instrument, start_date)
        # considering this is for spot and we need atleast last month of data, we will need to fetch data from start_date - 1 month
        self.read_spot_data(instrument, end_date)

        # date_to_fetch = datetime_to_fetch.strftime("%Y-%m-%d")
        # time_to_fetch = datetime_to_fetch.strftime("%H:%M:%S")
        # start_date = start_date.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        # end_date = end_date.strptime(end_date, "%Y-%m-%d %H:%M:%S")

        # if len(self.spot_data_df[(self.spot_data_df['<ticker>']==self.option_name[instrument]) & (self.spot_data_df['datetime']>=start_date) & (self.spot_data_df['datetime'] < end_date)])>0:
        sel_df = self.spot_data_df[(self.spot_data_df['<ticker>'] == self.option_name[instrument]) & (
                    self.spot_data_df['datetime'] >= start_date) & (self.spot_data_df['datetime'] < end_date)]
        # esle:

        # get the close date for a given date and time bi filtering the dataframe

        # print count of rows where date equals date
        # print('count of rows where date equals date ', len(self.spot_data_df[(self.spot_data_df['<date>'] == date_to_fetch)]))
        # print count of rows where time equals time
        # print('count of rows where time equals time ', len(self.spot_data_df[(self.spot_data_df['<time>'] == time_to_fetch)]))

        # if len(self.spot_data_df[(self.spot_data_df['<ticker>']==self.option_name[instrument]) & (self.spot_data_df['<date>'] == date_to_fetch) & (self.spot_data_df['<time>'] == time_to_fetch)])>0:
        #	close_price = list(self.spot_data_df[(self.spot_data_df['<ticker>']==self.option_name[instrument]) & (self.spot_data_df['<date>'] == date_to_fetch) & (self.spot_data_df['<time>'] == time_to_fetch)]['<close>'])[0]
        # else:
        #	close_price = -1

        return sel_df

    def get_live_ltp_option(self, instrument, datetime_to_fetch):
        ##http://localhost:4000/ltp?instrument=NFO:BANKNIFTY21JANFUT
        url = "http://localhost:4000/ltp?instrument=" + instrument
        try:
            resp = requests.get(url)
        except Exception as e:
            print(e)
        data = resp.json()
        return data

    def read_historical_option_data(self, instrument, datetime_to_fetch):
        date_to_fetch = datetime_to_fetch.strftime("%Y-%m-%d")
        # create only time from datetime_to_fetch
        time_to_fetch = datetime_to_fetch.strftime("%H:%M:%S")
        # get year from date
        year_to_fetch = datetime_to_fetch.strftime("%Y")
        # get month from	date
        month_to_fetch = datetime_to_fetch.strftime("%m")
        # get name of the month from above month date
        month_name_to_fetch = datetime_to_fetch.strftime("%B")
        yearmo_to_fetch = year_to_fetch + '_' + month_to_fetch

        path_to_fetch = None
        if Source == 0 or Source == 'SQL':
            path_to_fetch = os.path.join(base_folder_for_hist_data, self._base_stock, year_to_fetch,
                                         month_name_to_fetch, instrument + '.csv')
        # self.option_data_df = pd.read_csv(path_to_fetch)
        # print('shape of data read ', self.option_data_df.shape)

        # write an if condition to check if instrument is equal to ticker and datetime_to_fetch is present in dataframe date
        #

        if self.option_data_df is None or len(self.option_data_df) == 0:
            try:
                if Source == 0 or Source == 'SQL':
                    self.cur_option_data_df = pd.read_csv(path_to_fetch)
                    if self.cur_option_data_df is None:
                        raise Exception()
                elif Source == 'GDrive':
                    self.cur_option_data_df = fetch_data_from_drive.read_historical_option_data_csv_file_from_drive(
                        instrument, month_name_to_fetch)
                    if self.cur_option_data_df is None:
                        raise Exception()
                elif Source == 'S3':
                    file_path = f'{year_to_fetch}/{month_name_to_fetch}/{instrument}.csv'
                    self.cur_option_data_df = Fetch_S3_Files().read_historical_option_from_s3(file_path)
                    if self.cur_option_data_df is None:
                        raise Exception()
            except Exception as e:
                print('this error has been generated as option data was not found : ', e)
                return 0
            # print(self.cur_option_data_df.head())
            print('shape of data read None', self.cur_option_data_df.shape)
            self.cur_option_data_df['<date>'] = pd.to_datetime(self.cur_option_data_df['<date>'],
                                                               format='mixed').dt.date
            self.cur_option_data_df['month_of_date'] = self.cur_option_data_df['<date>'].apply(
                lambda x: x.strftime('%m'))
            self.cur_option_data_df['year_of_date'] = self.cur_option_data_df['<date>'].apply(
                lambda x: x.strftime('%Y'))
            self.cur_option_data_df['yearmo'] = self.cur_option_data_df['year_of_date'] + '_' + self.cur_option_data_df[
                'month_of_date']
            # convert the date to this format '%y-%m-%d'
            self.cur_option_data_df['<date>'] = self.cur_option_data_df['<date>'].apply(
                lambda x: x.strftime('%Y-%m-%d'))
            # convert time column to time
            self.cur_option_data_df['<time>'] = pd.to_datetime(self.cur_option_data_df['<time>'],
                                                               format='%H:%M:%S').dt.time
            # convert time to this string time format '%H:%M:%S'
            self.cur_option_data_df['<time>'] = self.cur_option_data_df['<time>'].apply(
                lambda x: x.strftime('%H:%M:%S'))
            # append cur_option data to option_data_df
            self.cur_option_data_df['datetime'] = pd.to_datetime(
                self.cur_option_data_df['<date>'] + ' ' + self.cur_option_data_df['<time>'])
            self.option_data_df = pd.concat([self.option_data_df, self.cur_option_data_df], ignore_index=True)
            print('shape after appending', self.option_data_df.shape)
        # create if condition to check if month_to_fetch and year_to_fetch are in the date column of option_data_df
        # and if instrument is in the ticker column of option_data_df
        # elif instrument in list(self.option_data_df['<ticker>']) and yearmo_to_fetch in list(pd.unique(self.option_data_df['yearmo'])):
        elif len(self.option_data_df[(self.option_data_df['<ticker>'] == instrument) & (
                self.option_data_df['yearmo'] == yearmo_to_fetch)]) > 0:
            # if instrument in list(self.option_data_df['<ticker>']) and datetime_to_fetch.strftime("%Y-%m-%d") in self.option_data_df['<date>'].values:
            temp = 0
            print('price has been found for this day options')
        else:
            try:
                if Source == 0 or Source == 'SQL':
                    self.cur_option_data_df = pd.read_csv(path_to_fetch)
                elif Source == 'GDrive':
                    self.cur_option_data_df = fetch_data_from_drive.read_historical_option_data_csv_file_from_drive(
                        instrument, month_name_to_fetch)
                    if self.cur_option_data_df is None:
                        raise Exception()
                elif Source == 'S3':
                    file_path = f'{year_to_fetch}/{month_name_to_fetch}/{instrument}.csv'
                    self.cur_option_data_df = Fetch_S3_Files().read_historical_option_from_s3(file_path)
                    if self.cur_option_data_df is None:
                        raise Exception()
            except Exception as e:
                print('this error has been generated as option data was not found : ', e)
                return 0
            print('shape of data read not found', self.cur_option_data_df.shape)
            self.cur_option_data_df['<date>'] = pd.to_datetime(self.cur_option_data_df['<date>'],
                                                               format='mixed').dt.date
            self.cur_option_data_df['month_of_date'] = self.cur_option_data_df['<date>'].apply(
                lambda x: x.strftime('%m'))
            self.cur_option_data_df['year_of_date'] = self.cur_option_data_df['<date>'].apply(
                lambda x: x.strftime('%Y'))
            self.cur_option_data_df['yearmo'] = self.cur_option_data_df['year_of_date'] + '_' + self.cur_option_data_df[
                'month_of_date']
            # convert the date to this format '%y-%m-%d'
            self.cur_option_data_df['<date>'] = self.cur_option_data_df['<date>'].apply(
                lambda x: x.strftime('%Y-%m-%d'))
            # convert time column to time
            self.cur_option_data_df['<time>'] = pd.to_datetime(self.cur_option_data_df['<time>'],
                                                               format='%H:%M:%S').dt.time
            # convert time to this string time format '%H:%M:%S'
            self.cur_option_data_df['<time>'] = self.cur_option_data_df['<time>'].apply(
                lambda x: x.strftime('%H:%M:%S'))
            self.cur_option_data_df['datetime'] = pd.to_datetime(
                self.cur_option_data_df['<date>'] + ' ' + self.cur_option_data_df['<time>'])
            self.option_data_df = pd.concat([self.option_data_df, self.cur_option_data_df], ignore_index=True)
            print('shape after appending', self.option_data_df.shape)
        return 0

    def get_historical_option(self, instrument, start_date, end_date):

        self.read_historical_option_data(instrument, start_date)
        self.read_historical_option_data(instrument, end_date)

        # convert start date to datetime format

        try:
            sel_df = self.option_data_df[
                (self.option_data_df['<ticker>'] == instrument) & (self.option_data_df['datetime'] >= start_date) & (
                            self.option_data_df['datetime'] < end_date)]
        except Exception as e:
            print('Exception raised while reading data in range data : ', e)
            return pd.DataFrame()

        # if len(self.option_data_df[(self.option_data_df['<ticker>']==instrument) & (self.option_data_df['<date>'] == date_to_fetch) & (self.option_data_df['<time>'] == time_to_fetch)])>0:
        #	close_price = list(self.option_data_df[ (self.option_data_df['<ticker>']==instrument) & (self.option_data_df['<date>'] == date_to_fetch) & (self.option_data_df['<time>'] == time_to_fetch) ]['<close>'])[0]
        # else:
        #	close_price = -1

        return sel_df


# write main function to fetch live data for BANKNIFTY
import datetime
import time

if __name__ == '__main__':
    # instantiate the class
    banknifty_object = RangeDataInterfaceLiveAndHistorical(live_data_fetch_flag=0)
    # create for loop to run 10 times
    datetime_to_fetch = datetime.datetime(2022, 7, 1, 10, 50, 0)

    # start_time = datetime.datetime(2022, 7, 1, 10, 50, 0)
    # end_time = datetime.datetime(2022, 8, 13, 10, 50, 0)

    # start_time = datetime.datetime(2022, 6, 3, 10, 50, 0)
    # end_time = datetime.datetime(2022, 7, 13, 10, 50, 0)

    start_time = datetime.datetime(2022, 7, 13, 10, 49, 0)
    end_time = datetime.datetime(2022, 7, 13, 10, 50, 0)

    # option_name = 'NIFTY23JUL19900PE'
    option_name = 'BANKNIFTY2271430000PE'
    # option_name_2 = 'BANKNIFTY2271430500PE'

    spot_df = banknifty_object.get_ltp_spot('BANKNIFTY', start_time, end_time)
    option_df = banknifty_object.get_ltp_option(option_name, start_time, end_time)

    print('spot price : ', spot_df.shape)
    print('option price : ', option_df.shape)

    # spot_df.to_csv(r'C:\Users\mdevaray\Documents\self\stock_market_project\Git_repos\pykiteconnect_repo\temp_data\range_spot_data_read.csv', index=False)
    # option_df.to_csv(r'C:\Users\mdevaray\Documents\self\stock_market_project\Git_repos\pykiteconnect_repo\temp_data\range_option_data_read.csv', index=False)

    print('------------- spot details below --------------')
    print('dates from and to : ', spot_df['datetime'].min(), '  to  ', spot_df['datetime'].max())

    print('----------  option data details below -----------------')
    print('dates from and to : ', option_df['datetime'].min(), '  to  ', option_df['datetime'].max())

# for i in range(50):
# call the function to fetch live data
# print('spot price : ',banknifty_object.get_ltp_spot('BANKNIFTY', start_time, end_time))
# print('option price : ',banknifty_object.get_ltp_option(option_name, datetime_to_fetch))
# print('option price 2 : ', banknifty_object.get_ltp_option(option_name_2, datetime_to_fetch))
# sleep for 5 seconds
# time.sleep(1)
# increment datetime by a minute
# datetime_to_fetch = datetime_to_fetch + datetime.timedelta(minutes=1)







