import pandas as pd
import requests
import os

#base_folder_for_hist_data = r'C:\Users\mdevaray\Documents\self\stock_market_project\Git_repos\pykiteconnect_repo\drive_data'
from config import base_directory_project

base_folder_for_hist_data = base_directory_project + "\\" + 'data'


import datetime



#write main function to fetch live data for BANKNIFTY
class DataInterfaceLiveAndHistorical():
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

		#instrument can contain these values ['NIFTY', 'BANKNIFTY']

	def get_ltp_spot(self, instrument, datetime_to_fetch):

		if self.live_data_fetch_flag == 1:
			if instrument == "BANKNIFTY":
				spot_name_updated_for_live = "NSE:"+"NIFTY BANK"
			elif instrument == "NIFTY":
				spot_name_updated_for_live = "NSE:"+instrument+" 50"
			else:
				spot_name_updated_for_live = ''
			return self.get_live_ltp_spot(spot_name_updated_for_live, datetime_to_fetch)
		else:
			return self.get_historical_ltp_spot(instrument, datetime_to_fetch)

	def get_ltp_option(self, instrument, datetime_to_fetch):
		if self.live_data_fetch_flag == 1:
			option_name_updated_for_live = "NFO:"+instrument
			return self.get_live_ltp_option(option_name_updated_for_live, datetime_to_fetch)
		else:
			return self.get_historical_ltp_option(instrument, datetime_to_fetch)

	def get_live_ltp_spot(self, instrument, datetime_to_fetch):
		url = "http://localhost:4000/ltp?instrument=" + instrument
		try:
			resp = requests.get(url)
		except Exception as e:
			print(e)
		data = resp.json()
		return data

	def get_historical_ltp_spot(self, instrument, datetime_to_fetch):

		year_to_fetch = datetime_to_fetch.strftime("%Y")
		#create this path: base_path/year/bank_nifty/.nsebkank.csv
		path_to_fetch_spot_data = os.path.join(base_folder_for_hist_data,'banknifty', year_to_fetch, 'Banknifty Spot Data', '.NSEBANK.csv')

		columns=['<ticker>','<date>','<time>','<open>','<high>','<low>','<close>','<volume>','<o/i> ']
		#read spot datafrom without header and assign above column names

		#check if self.spot_data_df is None or len=0 then read the csv file
		if (self.spot_data_df is None) or (len(self.spot_data_df)==0):
			print('reading spot')
			self.cur_spot_data_df = pd.read_csv(path_to_fetch_spot_data, header=None, names=columns)
			#convert date column to date datatype and get only date with format %y-%m-%d
			#self.cur_spot_data_df['<date>'] = pd.to_datetime(self.cur_spot_data_df['<date>'],format='mixed').dt.date
			#self.cur_spot_data_df['<date>'] = pd.to_datetime(self.cur_spot_data_df['<date>'], format='%d-%m-%Y').dt.date

			try:
				self.cur_spot_data_df['<date>'] = pd.to_datetime(self.cur_spot_data_df['<date>'], format='%Y/%m/%d').dt.date
			except Exception as e:
				try:
					self.cur_spot_data_df['<date>'] = pd.to_datetime(self.cur_spot_data_df['<date>'], format='%d-%m-%Y').dt.date
				except Exception as e:
					raise e

			#convert the date to this format '%y-%m-%d'
			self.cur_spot_data_df['<date>'] = self.cur_spot_data_df['<date>'].apply(lambda x: x.strftime('%Y-%m-%d'))
			#convert time column to time
			self.cur_spot_data_df['<time>'] = pd.to_datetime(self.cur_spot_data_df['<time>'], format='mixed').dt.time
			#convert time to this string time format '%H:%M:%S'
			self.cur_spot_data_df['<time>'] = self.cur_spot_data_df['<time>'].apply(lambda x: x.strftime('%H:%M:%S'))
			#write elseif condition to check if instrument is equal to ticker and datetime_to_fetch is present in dataframe date
			#append cur_spot_data_df to self.spot_data_df using concat
			self.spot_data_df = pd.concat([self.spot_data_df, self.cur_spot_data_df], ignore_index=True)

		#elif  self.option_name[instrument] == self.spot_data_df['<ticker>'][0] and datetime_to_fetch.strftime("%Y-%m-%d") in self.spot_data_df['<date>'].values:
		elif  self.option_name[instrument] in list(pd.unique(self.spot_data_df['<ticker>'])) and datetime_to_fetch.strftime("%Y-%m-%d") in self.spot_data_df['<date>'].values:
			temp = 0
			#print('no need to read')
		else:
			print('reading spot')
			#.NSEBANK
			self.cur_spot_data_df = pd.read_csv(path_to_fetch_spot_data, header=None, names=columns)
			#convert date column to date datatype and get only date with format %y-%m-%d
			#self.cur_spot_data_df['<date>'] = pd.to_datetime(self.cur_spot_data_df['<date>']).dt.date
			#self.cur_spot_data_df['<date>'] = pd.to_datetime(self.cur_spot_data_df['<date>'], format='%d-%m-%Y').dt.date

			try:
				self.cur_spot_data_df['<date>'] = pd.to_datetime(self.cur_spot_data_df['<date>'], format='%Y/%m/%d').dt.date
			except Exception as e:
				try:
					self.cur_spot_data_df['<date>'] = pd.to_datetime(self.cur_spot_data_df['<date>'], format='%d-%m-%Y').dt.date
				except Exception as e:
					raise e

			#convert the date to this format '%y-%m-%d'
			self.cur_spot_data_df['<date>'] = self.cur_spot_data_df['<date>'].apply(lambda x: x.strftime('%Y-%m-%d'))
			#convert time column to time
			self.cur_spot_data_df['<time>'] = pd.to_datetime(self.cur_spot_data_df['<time>'], format='mixed').dt.time
			#convert time to this string time format '%H:%M:%S'
			self.cur_spot_data_df['<time>'] = self.cur_spot_data_df['<time>'].apply(lambda x: x.strftime('%H:%M:%S'))
			#write elseif condition to check if instrument is equal to ticker and datetime_to_fetch is present in dataframe date
			self.spot_data_df = pd.concat([self.spot_data_df, self.cur_spot_data_df], ignore_index=True)


		#create date value to fetch
		date_to_fetch = datetime_to_fetch.strftime("%Y-%m-%d")
		#create only time from datetime_to_fetch
		time_to_fetch = datetime_to_fetch.strftime("%H:%M:%S")
		#print(' date and time : ', date_to_fetch, ' : ',time_to_fetch)

		#get the close date for a given date and time bi filtering the dataframe

		#print count of rows where date equals date
		#print('count of rows where date equals date ', len(self.spot_data_df[(self.spot_data_df['<date>'] == date_to_fetch)]))
		#print count of rows where time equals time
		#print('count of rows where time equals time ', len(self.spot_data_df[(self.spot_data_df['<time>'] == time_to_fetch)]))

		if len(self.spot_data_df[(self.spot_data_df['<ticker>']==self.option_name[instrument]) & (self.spot_data_df['<date>'] == date_to_fetch) & (self.spot_data_df['<time>'] == time_to_fetch)])>0:
			close_price = list(self.spot_data_df[(self.spot_data_df['<ticker>']==self.option_name[instrument]) & (self.spot_data_df['<date>'] == date_to_fetch) & (self.spot_data_df['<time>'] == time_to_fetch)]['<close>'])[0]
		else:
			close_price = -1

		return close_price

	def get_live_ltp_option(self, instrument, datetime_to_fetch):
		##http://localhost:4000/ltp?instrument=NFO:BANKNIFTY21JANFUT
		url = "http://localhost:4000/ltp?instrument=" + instrument
		try:
			resp = requests.get(url)
		except Exception as e:
			print(e)
		data = resp.json()
		return data

	def get_historical_ltp_option(self, instrument, datetime_to_fetch):
		date_to_fetch = datetime_to_fetch.strftime("%Y-%m-%d")
		#create only time from datetime_to_fetch
		time_to_fetch = datetime_to_fetch.strftime("%H:%M:%S")
		#get year from date
		year_to_fetch = datetime_to_fetch.strftime("%Y")
		#get month from	date
		month_to_fetch = datetime_to_fetch.strftime("%m")
		#get name of the month from above month date
		month_name_to_fetch = datetime_to_fetch.strftime("%B")


		path_to_fetch = os.path.join(base_folder_for_hist_data,self._base_stock, year_to_fetch, month_name_to_fetch, instrument + '.csv')
		#self.option_data_df = pd.read_csv(path_to_fetch)
		#print('shape of data read ', self.option_data_df.shape)

		#write an if condition to check if instrument is equal to ticker and datetime_to_fetch is present in dataframe date
		#

		if self.option_data_df is None or len(self.option_data_df)==0:
			self.cur_option_data_df = pd.read_csv(path_to_fetch)
			print('shape of data read ', self.cur_option_data_df.shape)
			self.cur_option_data_df['<date>'] = pd.to_datetime(self.cur_option_data_df['<date>']).dt.date
			#convert the date to this format '%y-%m-%d'
			self.cur_option_data_df['<date>'] = self.cur_option_data_df['<date>'].apply(lambda x: x.strftime('%Y-%m-%d'))
			#convert time column to time
			self.cur_option_data_df['<time>'] = pd.to_datetime(self.cur_option_data_df['<time>'], format='%H:%M:%S').dt.time
			#convert time to this string time format '%H:%M:%S'
			self.cur_option_data_df['<time>'] = self.cur_option_data_df['<time>'].apply(lambda x: x.strftime('%H:%M:%S'))
			#append cur_option data to option_data_df
			self.option_data_df = pd.concat([self.option_data_df, self.cur_option_data_df], ignore_index=True)
		if instrument in list(self.option_data_df['<ticker>']):#[0]: and datetime_to_fetch.strftime("%Y-%m-%d") in self.option_data_df['<date>'].values:
			temp = 0
			#print('price has been found for this day')
		else:
			self.cur_option_data_df = pd.read_csv(path_to_fetch)
			print('shape of data read ', self.option_data_df.shape)
			self.cur_option_data_df['<date>'] = pd.to_datetime(self.cur_option_data_df['<date>']).dt.date
			#convert the date to this format '%y-%m-%d'
			self.cur_option_data_df['<date>'] = self.cur_option_data_df['<date>'].apply(lambda x: x.strftime('%Y-%m-%d'))
			#convert time column to time
			self.cur_option_data_df['<time>'] = pd.to_datetime(self.cur_option_data_df['<time>'], format='%H:%M:%S').dt.time
			#convert time to this string time format '%H:%M:%S'
			self.cur_option_data_df['<time>'] = self.cur_option_data_df['<time>'].apply(lambda x: x.strftime('%H:%M:%S'))
			self.option_data_df = pd.concat([self.option_data_df, self.cur_option_data_df], ignore_index=True)

		if len(self.option_data_df[(self.option_data_df['<ticker>']==instrument) & (self.option_data_df['<date>'] == date_to_fetch) & (self.option_data_df['<time>'] == time_to_fetch)])>0:
			close_price = list(self.option_data_df[ (self.option_data_df['<ticker>']==instrument) & (self.option_data_df['<date>'] == date_to_fetch) & (self.option_data_df['<time>'] == time_to_fetch) ]['<close>'])[0]
		else:
			close_price = -1

		return close_price
import time
if __name__ == '__main__':
	#instantiate the class
	banknifty_object = DataInterfaceLiveAndHistorical(live_data_fetch_flag=0)
	#create for loop to run 10 times
	datetime_to_fetch = datetime.datetime(2022, 7, 1, 10, 50, 0)
	#option_name = 'NIFTY23JUL19900PE'
	option_name = 'BANKNIFTY2271430000PE'
	option_name_2 = 'BANKNIFTY2271430500PE'
	for i in range(50):
		#call the function to fetch live data
		print('spot price : ',banknifty_object.get_ltp_spot('BANKNIFTY', datetime_to_fetch))
		print('option price : ',banknifty_object.get_ltp_option(option_name, datetime_to_fetch))
		print('option price 2 : ', banknifty_object.get_ltp_option(option_name_2, datetime_to_fetch))





		#sleep for 5 seconds
		#time.sleep(1)
		#increment datetime by a minute
		datetime_to_fetch = datetime_to_fetch + datetime.timedelta(minutes=1)







