import pandas as pd

from src.trading_algo.data_interface.range_data_interface_for_live_and_historical import RangeDataInterfaceLiveAndHistorical
from src.trading_algo.option_contract_naming.get_closest_expiry_contract import get_closest_expiry

from src.trading_algo.metrics_calculation.sma_metrics_ta import SMA_Metrics_TA

from src.trading_algo.orderbook_storage.orderbook_storage_class import orderbookstorage

from datetime import timedelta
import datetime



#test_data_output_path = r'C:\Users\mdevaray\Documents\self\stock_market_project\Git_repos\pykiteconnect_repo\temp_data\trade_algo_sma'

#the entire class will be created and run for each data separately, so each day is individual and independent of each other
class trade_algo_structure():
	def __init__(self, base_stock_name, datetime_of_algo_execution): #send datetime of algo execution at 9:30 am
		self.base_stock_name = base_stock_name
		self.datetime_of_algo_execution = datetime_of_algo_execution
		self.datatime_of_lookback_start = self.datetime_of_algo_execution - timedelta(days=25)
		
		self.base_stock_data = pd.DataFrame()
		#self.ce_option_stock_data = pd.DataFrame()
		#self.pe_option_stock_data = pd.DataFrame()

		self.option_stock_data = {}
		self.live_trading = 0
		self.otm_for_option = 300



		self.data_interval_in_minutes = 1

		self._primary_ce_option_name = ''
		self._primary_pe_option_name = ''

		#we will select options which are relevant to the strategy something like bull call spread or bear put spread or short straddle etc
		self._pattern_for_option_selection_for_strategy = [{'type': 'CE', 'sel_criteria': 'strike_price', 'itm_atm_otm': 'otm', 'delta_strike_price': -300, 'option_name': '', 'execution_strategy': {'simple_selling': {'short_action': 'SELL'}}},
														   {'type': 'PE', 'sel_criteria': 'strike_price', 'itm_atm_otm': 'otm','delta_strike_price': -300, 'option_name': '', 'execution_strategy': {'simple_selling': {'long_action': 'SELL'}}}]

		self.selected_option_strategy = 'simple_selling'
		self.order_book_name = 'sma_trade_orderbook_updated_structure'
		self._options_selected_names = []
		self.option_execution_status_list = []
		self.options_list_to_execute = []

		self.data_source_obj = RangeDataInterfaceLiveAndHistorical(live_data_fetch_flag=self.live_trading)


		self.entry_status = {'exist': 0, 'long_position': 0}

		self.trade_status = 'closed' #'open', 'closed'

		self.stop_loss_points = 20
		#self.target_points = 100
		self.target_points = 400# this is with trailing stop loss
		self.stop_loss_price = 0
		self.target_price = 0

		self.combined_stop_loss_points = 30
		self.combined_target_points = 400
		
		self.option_entry_price = 0
		self.cur_trading_option = ''

		self.option_execution_dict = {}

		self.prev_datetime = None
		self.orderbook_obj = None
		
		#at the end of the code execute this to write_orderbook_data_to_disk, we might need to consider writing to disk after every exit trade because we might have mutiple entries in a day
		#self.orderbook_obj = orderbookstorage() orderbook_obj.write_orderbook_data_to_disk()

		#initialize all the dataframes with necessary data, and probably fetch the first 15 minutes candle data as a default and start trading from the 9:30 candle for the day

	def get_suitable_option_contract_name(self, base_stock_name,ce_or_pe, recent_stock_price, recent_datetime, otm):
		if base_stock_name == "BANKNIFTY":
			closest_Strike = int(round((recent_stock_price / 100),0) * 100)
			print(closest_Strike)
		elif base_stock_name == "NIFTY":
			closest_Strike = int(round((recent_stock_price / 50),0) * 50)
			print(closest_Strike)

		print("closest ",closest_Strike)
		closest_Strike_CE = closest_Strike+otm
		closest_Strike_PE = closest_Strike+otm

		expiry_name_object = get_closest_expiry()
		next_closest_thursday = expiry_name_object.get_next_closest_weekly_expiry(recent_datetime)
		atmCE = expiry_name_object.get_option_contract_name(base_stock_name, next_closest_thursday, closest_Strike_CE, 'CE')
		atmPE = expiry_name_object.get_option_contract_name(base_stock_name, next_closest_thursday, closest_Strike_PE, 'PE')

		if ce_or_pe=='CE':
			return atmCE
		else:
			return atmPE

	def data_initialization(self):
		#fetch data for instrument for the given data of exection, fetch last 1 month data
		#also fetch first 15 minutes of data for the day so that strike price can be calculated and the algo can start trading from 9:30 candle
		#also fetch the data for the option strike price for the given instrument
		self.data_initialize_base_stock()


		#get the price of the most recent datetime in base_stock_data
		recent_datetime = self.base_stock_data['datetime'].max()
		#recent_stock_price = list(self.base_stock_data['<close>'])[len(self.base_stock_data)-1]
		recent_stock_price = list(self.base_stock_data[self.base_stock_data['datetime']==recent_datetime]['<close>'])[0]

		self.load_options_watchlist_names(recent_stock_price, recent_datetime)

		# print('CE name : ', self._primary_ce_option_name)
		# print('PE name : ', self._primary_pe_option_name)

		# self.data_initialize_option_stock(self._primary_ce_option_name)
		# self.data_initialize_option_stock(self._primary_pe_option_name)

		for option_name in self._options_selected_names:
			self.data_initialize_option_stock(option_name)


	def load_options_watchlist_names(self, recent_stock_price, recent_datetime):
		# self._primary_ce_option_name = self.get_suitable_option_contract_name(self.base_stock_name,'CE',
		# 									recent_stock_price, recent_datetime, self.otm_for_option)
		# self._primary_pe_option_name = self.get_suitable_option_contract_name(self.base_stock_name,'PE',
		# 								  	recent_stock_price, recent_datetime, self.otm_for_option)

		for option_pattern in self._pattern_for_option_selection_for_strategy:
			if option_pattern['type']=='CE':
				if option_pattern['itm_atm_otm']=='otm':
					option_name_calculated = self.get_suitable_option_contract_name(self.base_stock_name, 'CE',
																							   recent_stock_price, recent_datetime, option_pattern['delta_strike_price'])

					self._options_selected_names.append(option_name_calculated)
					option_pattern['option_name'] = option_name_calculated
				else:
					option_name_calculated = self.get_suitable_option_contract_name(self.base_stock_name, 'CE',
																							   recent_stock_price, recent_datetime, -1 * option_pattern['delta_strike_price'])

					self._options_selected_names.append(option_name_calculated)
					option_pattern['option_name'] = option_name_calculated

			if option_pattern['type'] == 'PE':
				if option_pattern['itm_atm_otm'] == 'otm':
					option_name_calculated = self.get_suitable_option_contract_name(self.base_stock_name, 'PE',
																							   recent_stock_price, recent_datetime, -1 * option_pattern['delta_strike_price'])
					self._options_selected_names.append(option_name_calculated)
					option_pattern['option_name'] = option_name_calculated
				else:
					option_name_calculated = self.get_suitable_option_contract_name(self.base_stock_name, 'PE',
																							   recent_stock_price, recent_datetime, option_pattern['delta_strike_price'])

					self._options_selected_names.append(option_name_calculated)
					option_pattern['option_name'] = option_name_calculated


	def data_initialize_base_stock(self):
		self.base_stock_data = self.data_source_obj.get_ltp_spot(self.base_stock_name, self.datatime_of_lookback_start, self.datetime_of_algo_execution)

		#self.base_stock_data.to_csv(test_data_output_path + '//' + 'base_stock_data_initialization.csv', index=False)


	def data_initialize_option_stock(self,option_name):
		sel_data = self.data_source_obj.get_ltp_option(option_name, self.datatime_of_lookback_start, self.datetime_of_algo_execution)
		#concat sel_data to the option_stock_data dataframe
		#check if option_name in option_stock_data dictionary, if not then create a new dataframe and add it to the dictionary, if present then append to the DataFrame
		if option_name not in self.option_stock_data.keys():
			self.option_stock_data[option_name] = sel_data
		else:
			#self.option_stock_data[option_name] = pd.concat([self.option_stock_data[option_name], sel_data], ignore_index=True)
			raise 'cannot initialise same option multiple times'

		#self.option_stock_data[option_name].to_csv(test_data_output_path + '//' + option_name +'_' + 'option_data_initialization.csv', index=False)

		#self.option_stock_data = pd.concat([self.option_stock_data, sel_data], ignore_index=True)

	def add_new_incremental_data(self, start_date, end_date):
		self.add_new_incremental_data_base_stock(start_date, end_date)
		self.add_new_incremental_data_options(start_date, end_date)

	def add_new_incremental_data_base_stock(self, start_date, end_date):
		
		sel_data = self.data_source_obj.get_ltp_spot(self.base_stock_name, start_date, end_date)
		#append sel_data to the base_stock_data dataframe

		if len(sel_data)>0:
			self.base_stock_data = pd.concat([self.base_stock_data, sel_data], ignore_index=True)


	def add_new_incremental_data_options(self, start_date, end_date):
		#this function could have multiple rows for same time if fetched multiple time for a same date range
		#iterate through the option_stock_data dictionary and get the ltp option data for each option_name and append to the dictionary item if its len>0
		for option_name in self.option_stock_data.keys():
			sel_data = self.data_source_obj.get_ltp_option(option_name, start_date, end_date)
			if len(sel_data)>0:
				self.option_stock_data[option_name] = pd.concat([self.option_stock_data[option_name], sel_data], ignore_index=True)

	#
	def calculate_incremental_metrics(self):
		self.base_stock_data = self.metrics_obj.calculate_metrics(self.base_stock_data)



	def get_options_execution_list(self, long_position):

		if long_position==1:
			entry_action_key = 'long_action'
		else:
			entry_action_key = 'short_action'

		for option_i in self._pattern_for_option_selection_for_strategy:
			if self.selected_option_strategy in option_i['execution_strategy'].keys():
				sel_option_name = option_i['option_name']
				execution_strategy_action = option_i['execution_strategy'][self.selected_option_strategy]
				option_type = option_i['type']
				if entry_action_key in execution_strategy_action.keys():
					option_execution_params = {'option_name': sel_option_name, 'type': option_type, 'position': entry_action_key,'entry_action': execution_strategy_action[entry_action_key]}
					self.options_list_to_execute.append(option_execution_params)




	def entry_execution(self, long_position):
		max_datetime = self.base_stock_data['datetime'].max()
		#if long_position == 1:
		# take long entry
		base_stock_entry_price = \
		list(self.base_stock_data[self.base_stock_data['datetime'] == max_datetime]['<close>'])[0]
		entry_datetime = max_datetime
		# self.base_stock_data.to_csv(test_data_output_path + '//' + 'testing_base_stock_data.csv',
		# 							index=False)
		# self.option_stock_data[self._primary_pe_option_name].to_csv(test_data_output_path + '//' + 'testing_option_data.csv',
		# 							index=False)

		try:
			# entry_option_price = list(self.option_stock_data[self._primary_pe_option_name][
			# 							  self.option_stock_data[self._primary_pe_option_name][
			# 								  'datetime'] == max_datetime]['<close>'])[0]
			self.get_options_execution_list(long_position)


			for option_to_execute in self.options_list_to_execute:
				option_name = option_to_execute['option_name']
				option_type = option_to_execute['type']
				trade_type = option_to_execute['position']
				entry_action = option_to_execute['entry_action']

				try:
					entry_option_price = list(self.option_stock_data[option_name][
												  self.option_stock_data[option_name][
													  'datetime'] == max_datetime]['<close>'])[0]
				except Exception as e:
					max_datetime_option = self.option_stock_data[option_name]['datetime'].max()

					entry_option_price = list(self.option_stock_data[option_name][
												  self.option_stock_data[option_name][
													  'datetime'] == max_datetime_option]['<close>'])[0]

					#return

				self.trade_status = 'open'

				#self.stop_loss_price = entry_option_price + self.stop_loss_points
				#self.target_price = max(entry_option_price - self.target_points, 0)

				sell_order_status = self.orderbook_obj._place_order_historical_data(variety='regular',
																					symb=option_name,
																					exch='NFO',
																					t_type=entry_action, qty=25,
																					order_type='MARKET',
																					product='MIS',
																					price=entry_option_price,
																					trigger_price=0,
																					time_of_trade=entry_datetime,
																					comments=trade_type)

				option_execution_status_i = {'option_name': option_name, 'trade_status': 'first_entry', 'option_type': option_type,
											 'entry_action': entry_action, 'long_position': long_position, 'stop_loss_points': 0,
											 'target_points': 0, 'stop_loss_price': 0, 'target_price': 0, 'entry_price':
												 entry_option_price, 'cur_pnl': 0, 'cur_price': entry_option_price }
				self.option_execution_status_list.append(option_execution_status_i)
		except Exception as e:
			print('exception raised while reading entry whole pipeline: ', e)
			return


	def evaluate_entry(self):

		# try:
		# 	cur_option_price = list(self.option_stock_data[option_name][self.option_stock_data[option_name]['datetime']==max_datetime]['<close>'])[0]
		# except Exception as e:
		# 	print('exception raised while reading : ', e)
		# 	return


		#print('cur entry time : ', max_datetime)
		if self.trade_status=='closed':
			self.check_if_entry_exists()
			if self.entry_status['exist']==1:
				self.entry_execution(self.entry_status['long_position'])

	# def update_running_trade(self):
	# 	max_datetime = self.base_stock_data['datetime'].max()
	# 	for option_to_update in self.option_execution_status_list:
	# 		if option_to_update['trade_status']=='first_entry':
	# 			option_to_update['stop_loss_points'] = self.stop_loss_points
	# 			option_to_update['target_points'] = self.target_points
	# 			option_to_update['trade_status'] = 'running'
	#
	# 			option_to_update['stop_loss_price'] = self.calc_stop_loss_price(option_to_update['entry_price'],
	# 										option_to_update['entry_action'], option_to_update['stop_loss_points'])
	# 			option_to_update['target_price'] = self.calc_target_price(option_to_update['entry_price'],
	# 										option_to_update['entry_action'], option_to_update['target_points'])
	# 		elif option_to_update['trade_status']=='running':
	# 			#update stop loss or any other parameters
	# 			#update the current price of all the options
	# 			temp = 0
	# 			# trailing stop loss
	# 			try:
	# 				entry_option_price = list(self.option_stock_data[option_to_update['option_name']][
	# 											  self.option_stock_data[option_to_update['option_name']][
	# 												  'datetime'] == max_datetime]['<close>'])[0]
	# 			except Exception as e:
	# 				print('exception raised while reading exit : ', e)
	# 				return
	#
	# 			option_to_update['cur_price'] = entry_option_price
	#
	# 			#trailing stop loss
	# 			if option_to_update['entry_action'] == 'SELL':
	# 				if option_to_update['cur_price'] < option_to_update['entry_price']:
	# 					new_stop_loss = option_to_update['cur_price'] + option_to_update['stop_loss_points']
	# 					option_to_update['stop_loss_price'] = min(option_to_update['stop_loss_price'], new_stop_loss)
	# 			elif option_to_update['entry_action'] == 'BUY':
	# 				if option_to_update['cur_price'] > option_to_update['entry_price']:
	# 					new_stop_loss = option_to_update['cur_price'] - option_to_update['stop_loss_points']
	# 					option_to_update['stop_loss_price'] = max(option_to_update['stop_loss_price'], new_stop_loss)
	# 			else:
	# 				raise 'incorrect entry_action value'


	def calc_stop_loss_price(self, base_price, position_type, stop_loss_points):
		if position_type=='BUY':
			stop_loss_price = base_price - stop_loss_points
		elif position_type=='SELL':
			stop_loss_price = base_price + stop_loss_points
		else:
			raise 'incorrect position type argument'

		return stop_loss_price

	def calc_target_price(self, base_price, position_type, target_points):
		if position_type=='BUY':
			target_price = base_price + target_points
		elif position_type=='SELL':
			target_price = base_price - target_points
		else:
			raise 'incorrect position type argument'

		return target_price

	def calc_pnl(self, entry_price, position_type, exit_type):
		if position_type=='BUY':
			cur_pnl = exit_type - entry_price
		elif position_type=='SELL':
			cur_pnl = entry_price - exit_type
		else:
			raise 'incorrect position type argument'

		return cur_pnl


	def get_position_type_for_exit(self, entry_position):
		if entry_position == 'BUY':
			return 'SELL'
		elif entry_position == 'SELL':
			return 'BUY'
		else:
			raise 'incorrect position argument'

	def place_exit_order(self, option_status_data, cur_datetime, exit_reason):
		sell_order_status = self.orderbook_obj._place_order_historical_data(variety='regular', symb=option_status_data['option_name'],
																			exch='NFO', t_type=self.get_position_type_for_exit(option_status_data['entry_action']), qty=25,
																			order_type='MARKET', product='MIS',
																			price = option_status_data['cur_price'], trigger_price=0,
																			time_of_trade=cur_datetime,
																			comments=exit_reason)

	# def evaluate_exit(self):
	# 	max_datetime = self.base_stock_data['datetime'].max()
	#
	# 	for option_to_execute in self.option_execution_status_list:
	# 		if option_to_execute['trade_status'] == 'running':
	# 			if option_to_execute['entry_action'] == 'SELL':
	# 				if option_to_execute['cur_price'] > option_to_execute['stop_loss_price']:
	# 					option_to_execute['trade_status'] = 'exited'
	# 					self.place_exit_order(option_to_execute, max_datetime, 'stop loss hit')
	# 				elif option_to_execute['cur_price'] < option_to_execute['target_price']:
	# 					option_to_execute['trade_status'] = 'exited'
	# 					self.place_exit_order(option_to_execute, max_datetime, 'Target hit')
	# 				elif max_datetime.hour == 14 and max_datetime.minute == 50:
	# 					option_to_execute['trade_status'] = 'exited'
	# 					self.place_exit_order(option_to_execute, max_datetime, 'EOD exit')
	# 			elif option_to_execute['entry_action'] == 'BUY':
	# 				if option_to_execute['cur_price'] < option_to_execute['stop_loss_price']:
	# 					option_to_execute['trade_status'] = 'exited'
	# 					self.place_exit_order(option_to_execute, max_datetime, 'stop loss hit')
	# 				elif option_to_execute['cur_price'] > option_to_execute['target_price']:
	# 					option_to_execute['trade_status'] = 'exited'
	# 					self.place_exit_order(option_to_execute, max_datetime, 'Target hit')
	# 				elif max_datetime.hour == 14 and max_datetime.minute == 50:
	# 					option_to_execute['trade_status'] = 'exited'
	# 					self.place_exit_order(option_to_execute, max_datetime, 'EOD exit')
	# 			else:
	# 				raise 'incorrect entry_action value'

		# option_name = self.cur_trading_option
		#
		# try:
		# 	cur_option_price = list(self.option_stock_data[option_name][self.option_stock_data[option_name]['datetime']==max_datetime]['<close>'])[0]
		# except Exception as e:
		# 	print('exception raised while reading exit : ', e)
		# 	return
		#
		# if cur_option_price>self.stop_loss_price:
		# 	#exit the trade due to stop loss
		# 	sell_order_status = self.orderbook_obj._place_order_historical_data(variety = 'regular', symb = option_name, exch = 'NFO', t_type = 'BUY', qty = 25, order_type = 'MARKET', product = 'MIS',price = cur_option_price, trigger_price = 0,time_of_trade = max_datetime,comments = 'stop loss hit')
		# 	self.trade_status = 'closed'
		# 	self.entry_status['exist'] = 0
		# 	self.orderbook_obj.write_orderbook_data_to_disk()
		# 	self.orderbook_obj = orderbookstorage('sma_trade_orderbook')
		# elif cur_option_price<self.target_price:
		# 	#exit the trade due to target hit
		# 	sell_order_status = self.orderbook_obj._place_order_historical_data(variety = 'regular', symb = option_name, exch = 'NFO', t_type = 'BUY', qty = 25, order_type = 'MARKET', product = 'MIS',price = cur_option_price, trigger_price = 0,time_of_trade = max_datetime,comments = 'Target hit')
		# 	self.trade_status = 'closed'
		# 	self.entry_status['exist'] = 0
		# 	self.orderbook_obj.write_orderbook_data_to_disk()
		# 	self.orderbook_obj = orderbookstorage('sma_trade_orderbook')
		# #write a condition to check if time in max_datetime is equal to 15:20:00, if so exit the trade
		# elif max_datetime.hour==14 and max_datetime.minute==50:
		# 	sell_order_status = self.orderbook_obj._place_order_historical_data(variety = 'regular', symb = option_name, exch = 'NFO', t_type = 'BUY', qty = 25, order_type = 'MARKET', product = 'MIS',price = cur_option_price, trigger_price = 0,time_of_trade = max_datetime,comments = 'EOD exit')
		# 	self.trade_status = 'closed'
		# 	self.entry_status['exist'] = 0
		# 	self.orderbook_obj.write_orderbook_data_to_disk()
		# 	self.orderbook_obj = orderbookstorage('sma_trade_orderbook')
		 

	def take_exit(self):
		max_datetime = self.base_stock_data['datetime'].max()

		if self.trade_status=='open':
			self.evaluate_exit()

	def check_overall_strategy_status(self):
		count_of_executing_options = 0
		existing_options = 0
		for option_executor in self.option_execution_status_list:
			existing_options += 1
			if option_executor['trade_status'] != 'exited':
				count_of_executing_options += 1
		if (count_of_executing_options == 0) and (existing_options>0):
			self.trade_status = 'closed'
			self.entry_status['exist'] = 0

			self.orderbook_obj.write_orderbook_data_to_disk()
			self.orderbook_obj = orderbookstorage(self.order_book_name)
			self.option_execution_status_list = []
			self.options_list_to_execute = []


	def running_trade_algo(self):

		self.data_initialization()
		self.orderbook_obj = orderbookstorage(self.order_book_name)
		self.initialise_metrics_obj()

		#create end_datetime as self.datetime_od_lookback with time=3:20:00
		end_datetime = self.datetime_of_algo_execution.replace(hour=15, minute=20, second=0)
		#create a loop from self.datetime_of_lookback to end_datetime by incrementing 1 minute
		cur_time = self.datetime_of_algo_execution
		#while(~(cur_time.hour==15 and cur_time.minute==21)):
		while(cur_time.hour!=15):
			self.add_new_incremental_data(cur_time, cur_time + datetime.timedelta(minutes=1))
			self.calculate_incremental_metrics()
			self.evaluate_entry()
			self.update_running_trade()
			self.take_exit()
			self.check_overall_strategy_status()

			#pending things: need to update global trade variables, write orderbook to disk
			#pending: also need to refresh current prices for all options in the execution list

			cur_time = cur_time + datetime.timedelta(minutes=1)



if __name__=="__main__":
	#back_test_start_date = datetime.datetime(2022, 3, 8, 9, 30, 0)# when this day is a holiday it could cause issue because it would read previous day data only
	#back_test_start_date = datetime.datetime(2022, 5, 1, 9, 30, 0)
	#back_test_start_date = datetime.datetime(2022, 2, 2, 9, 30, 0)
	#back_test_start_date = datetime.datetime(2022, 6, 29, 9, 30, 0)
	back_test_start_date = datetime.datetime(2022, 7, 20, 9, 30, 0)
	#back_test_start_date = datetime.datetime(2022, 7, 25, 9, 30, 0)
	#back_test_start_date = datetime.datetime(2022, 3, 8, 9, 30, 0)
	#back_test_start_date = datetime.datetime(2022, 6, 29, 9, 30, 0)
	#back_test_start_date = datetime.datetime(2022, 4, 7, 9, 30, 0)
	#back_test_start_date = datetime.datetime(2022, 5, 21, 9, 30, 0)
	#back_test_start_date = datetime.datetime(2022, 5, 24, 9, 30, 0)
	#back_test_start_date = datetime.datetime(2022, 5, 25, 9, 30, 0)
	#back_test_end_date = datetime.datetime(2022, 2, 10, 9, 30, 0)
	#back_test_end_date = datetime.datetime(2022, 7, 20, 9, 30, 0)
	back_test_end_date = datetime.datetime(2022, 7, 30, 9, 30, 0)
	#back_test_end_date = datetime.datetime(2022, 7, 21, 9, 30, 0)




	#data_interface_obj = trade_algo_structure('BANKNIFTY', back_test_start_date).running_trade_algo()
	#exit(0)

	#create a loop from start_date to end_date by incrementing one day
	cur_date = back_test_start_date
	while(cur_date<=back_test_end_date):
		print('running for the date : ', cur_date)
		data_interface_obj = trade_algo_structure('BANKNIFTY', cur_date).running_trade_algo()
		cur_date = cur_date + datetime.timedelta(days=1)



	#
	# def add_data_for_a_given_row(self, instrument_name, datetime_to_fetch, type_of_ins): #type_of_ins=['stock','option']
	# 	#add the data for that instrument from max_datetie for instruemnt to the given datetime_to_fetch
	# 	#add the data to the respective dataframe
	#
	# 	#convert datetime_to_fetch to the format and seconds=00
	# 	datetime_to_fetch = datetime_to_fetch.strftime('%Y-%m-%d %H:%M:00')
	#
	# 	if type_of_ins == 'stock':
	# 		#fetch data for the given instrument from the max datetime for that instrument to the given datetime_to_fetch
	# 		#add the data to the base_stock_data dataframe
	#
	# 		#check if instrument_name and datetime_to_fetch is already present in the dataframe
	# 		if len(self.base_stock_data[(self.base_stock_data['<ticker>']==instrument_name)]) == 0:
	# 			start_date_to_fetch_data = self.data_start_date
	# 			end_date_to_fetch_data = datetime_to_fetch
	# 		elif len(self.base_stock_data[(self.base_stock_data['<ticker>']==instrument_name) & (self.base_stock_data['datetime']==datetime_to_fetch)]) == 0:
	# 			#get max date for this instrument in the data
	# 			max_date_for_instrument = max(self.base_stock_data[(self.base_stock_data['<ticker>']==instrument_name)]['datetime'])
	# 			start_date_to_fetch_data = max_date_for_instrument
	# 			end_date_to_fetch_data = datetime_to_fetch
	#
	#
	#
	#
	# 	elif type_of_ins == 'option':
	# 		#fetch data for the given instrument from the max datetime for that instrument to the given datetime_to_fetch
	# 		#add the data to the option_stock_data dataframe

























