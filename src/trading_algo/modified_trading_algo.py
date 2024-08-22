import pandas as pd

from src.trading_algo.range_data_interface_for_live_and_historical import RangeDataInterfaceLiveAndHistorical
from src.trading_algo.get_closest_expiry_contract import get_closest_expiry
from src.trading_algo.source import Source
from src.trading_algo.metrics_calculation.sma_metrics_ta import SMA_Metrics_TA
# from src.trading_algo.metrics_calculation.supertrend_metrics_ta import Supertrend_Metrics_TA

from src.trading_algo.orderbook_storage_class import orderbookstorage

from src.trading_algo.fetch_data_from_drive import upload_base_stock_data_with_metrics
from src.trading_algo.option_parameters_fetching import option_parameters
from src.trading_algo.fetch_data_from_S3 import Fetch_S3_Files
from datetime import timedelta
import datetime

from config import base_directory_project

test_data_output_path = base_directory_project + "/" + 'output'


# test_data_output_path = r'C:\Users\mdevaray\Documents\self\stock_market_project\Git_repos\pykiteconnect_repo\temp_data\trade_algo_sma'

# the entire class will be created and run for each data separately, so each day is individual and independent of each other
class trade_algo_structure():
    def __init__(self, base_stock_name, datetime_of_algo_execution, pattern_for_option_selection):  # send datetime of algo execution at 9:30 am
        self.base_stock_name = base_stock_name
        self.datetime_of_algo_execution = datetime_of_algo_execution
        self.datatime_of_lookback_start = self.datetime_of_algo_execution - timedelta(days=25)

        self.base_stock_data = pd.DataFrame()
        # self.ce_option_stock_data = pd.DataFrame()
        # self.pe_option_stock_data = pd.DataFrame()

        self.option_stock_data = {}
        self.live_trading = 0
        self.otm_for_option = 300
        self._pattern_for_option_selection_for_strategy = pattern_for_option_selection
        # self._pattern_for_option_selection_for_strategy = [{'type': 'CE', 'sel_criteria': 'strike_price', 'itm_atm_otm': 'otm', 'delta_strike_price': -300, 'option_name': '', 'execution_strategy': {'simple_selling': {'short_action': 'SELL'}}},
        #                                 {'type': 'PE', 'sel_criteria': 'strike_price', 'itm_atm_otm': 'otm','delta_strike_price': -300, 'option_name': '', 'execution_strategy': {'simple_selling': {'long_action': 'SELL'}}}]

        self.data_interval_in_minutes = 1

        self._primary_ce_option_name = ''
        self._primary_pe_option_name = ''

        self.data_source_obj = RangeDataInterfaceLiveAndHistorical(live_data_fetch_flag=self.live_trading)
        self.data_initialization()

        self.metrics_obj = SMA_Metrics_TA(200)
        self.metrics_col_name = 'SMA_value'

        # self.metrics_obj = Supertrend_Metrics_TA(10,3)
        # self.metrics_col_name = 'Supertrend_value'

        self.entry_status = {'exist': 0, 'long_position': 0}

        self.trade_status = 'closed'  # 'open', 'closed'

        self.orderbook_obj = orderbookstorage('sma_trade_orderbook')

        self.stop_loss_points = 20
        # self.target_points = 100
        self.target_points = 400  # this is with trailing stop loss
        self.stop_loss_price = 0
        self.target_price = 0

        self.option_entry_price = 0
        self.cur_trading_option = ''

        self.prev_datetime = None

    # at the end of the code execute this to write_orderbook_data_to_disk, we might need to consider writing to disk after every exit trade because we might have mutiple entries in a day
    # self.orderbook_obj = orderbookstorage() orderbook_obj.write_orderbook_data_to_disk()

    # initialize all the dataframes with necessary data, and probably fetch the first 15 minutes candle data as a default and start trading from the 9:30 candle for the day
    
    def get_suitable_option_contract_name(self, base_stock_name, ce_or_pe, recent_stock_price, recent_datetime, otm, delta_strike_price):
        if base_stock_name == "BANKNIFTY":
            closest_Strike = int(round((recent_stock_price / 100), 0) * 100)
            print(closest_Strike)
        elif base_stock_name == "NIFTY":
            closest_Strike = int(round((recent_stock_price / 50), 0) * 50)
            print(closest_Strike)

        print("closest ", closest_Strike)
        
        closest_Strike_CE = closest_Strike + otm
        closest_Strike_PE = closest_Strike - otm

        expiry_name_object = get_closest_expiry()
        next_closest_thursday = expiry_name_object.get_next_closest_weekly_expiry(recent_datetime)
        atmCE = expiry_name_object.get_option_contract_name(base_stock_name, next_closest_thursday, closest_Strike_CE,
                                                            'CE')
        atmPE = expiry_name_object.get_option_contract_name(base_stock_name, next_closest_thursday, closest_Strike_PE,
                                                            'PE')

        if ce_or_pe == 'CE':
            return atmCE
        else:
            return atmPE

    def data_initialization(self):
        # fetch data for instrument for the given data of exection, fetch last 1 month data
        # also fetch first 15 minutes of data for the day so that strike price can be calculated and the algo can start trading from 9:30 candle
        # also fetch the data for the option strike price for the given instrument
        self.data_initialize_base_stock()
        
        # get the price of the most recent datetime in base_stock_data
        recent_datetime = self.base_stock_data['datetime'].max()
        # recent_stock_price = list(self.base_stock_data['<close>'])[len(self.base_stock_data)-1]
        recent_stock_price = list(self.base_stock_data[self.base_stock_data['datetime'] == recent_datetime]['<close>'])[
            0]
        
        delta_strike_price_pe = self._pattern_for_option_selection_for_strategy['PE']['delta_strike_price_pe']
        delta_strike_price_ce = self._pattern_for_option_selection_for_strategy['CE']['delta_strike_price_ce']
        
        self._primary_ce_option_name = self.get_suitable_option_contract_name(self.base_stock_name, 'CE',
                                                                              recent_stock_price, recent_datetime,
                                                                              self.otm_for_option, delta_strike_price_ce)
        self._primary_pe_option_name = self.get_suitable_option_contract_name(self.base_stock_name, 'PE',
                                                                              recent_stock_price, recent_datetime,
                                                                              self.otm_for_option, delta_strike_price_pe)
        print('CE name : ', self._primary_ce_option_name)
        print('PE name : ', self._primary_pe_option_name)

        self.data_initialize_option_stock(self._primary_ce_option_name)
        self.data_initialize_option_stock(self._primary_pe_option_name)
        
    def data_initialize_base_stock(self):
        self.base_stock_data = self.data_source_obj.get_ltp_spot(self.base_stock_name, self.datatime_of_lookback_start,
                                                                 self.datetime_of_algo_execution)

    # self.base_stock_data.to_csv(test_data_output_path + '//' + 'base_stock_data_initialization.csv', index=False)

    def data_initialize_option_stock(self, option_name):
        sel_data = self.data_source_obj.get_ltp_option(option_name, self.datatime_of_lookback_start,
                                                       self.datetime_of_algo_execution)
        # concat sel_data to the option_stock_data dataframe
        # check if option_name in option_stock_data dictionary, if not then create a new dataframe and add it to the dictionary, if present then append to the DataFrame
        if option_name not in self.option_stock_data.keys():
            self.option_stock_data[option_name] = sel_data
        else:
            self.option_stock_data[option_name] = pd.concat([self.option_stock_data[option_name], sel_data],
                                                            ignore_index=True)

    # self.option_stock_data[option_name].to_csv(test_data_output_path + '//' + option_name +'_' + 'option_data_initialization.csv', index=False)

    # self.option_stock_data = pd.concat([self.option_stock_data, sel_data], ignore_index=True)

    def add_new_incremental_data(self, start_date, end_date):
        self.add_new_incremental_data_base_stock(start_date, end_date)
        self.add_new_incremental_data_options(start_date, end_date)

    def add_new_incremental_data_base_stock(self, start_date, end_date):

        sel_data = self.data_source_obj.get_ltp_spot(self.base_stock_name, start_date, end_date)
        # append sel_data to the base_stock_data dataframe

        if len(sel_data) > 0:
            self.base_stock_data = pd.concat([self.base_stock_data, sel_data], ignore_index=True)

    def add_new_incremental_data_options(self, start_date, end_date):

        # iterate through the option_stock_data dictionary and get the ltp option data for each option_name and append to the dictionary item if its len>0
        for option_name in self.option_stock_data.keys():
            sel_data = self.data_source_obj.get_ltp_option(option_name, start_date, end_date)
            if len(sel_data) > 0:
                self.option_stock_data[option_name] = pd.concat([self.option_stock_data[option_name], sel_data],
                                                                ignore_index=True)

    #
    def calculate_incremental_metrics(self):
        self.base_stock_data = self.metrics_obj.calculate_metrics(self.base_stock_data)

    def check_if_entry_exists(self):
        # get max value of datetime from the base_stock_data
        max_datetime = self.base_stock_data['datetime'].max()
        prev_datetime = max_datetime - datetime.timedelta(minutes=1)

        # get the close value for the max_datetime
        max_close = list(self.base_stock_data[self.base_stock_data['datetime'] == max_datetime]['<close>'])[0]
        metric_value = \
        list(self.base_stock_data[self.base_stock_data['datetime'] == max_datetime][self.metrics_col_name])[0]

        prev_max_close = list(self.base_stock_data[self.base_stock_data['datetime'] == prev_datetime]['<close>'])[0]
        prev_metric_value = \
        list(self.base_stock_data[self.base_stock_data['datetime'] == prev_datetime][self.metrics_col_name])[0]

        # for SMA_Metrics_TA
        # check if metric value is greater than max_close, if yes then update entry_status dict to 1
        if (metric_value >= max_close) and (prev_metric_value < prev_max_close):
            self.entry_status['exist'] = 1
            self.entry_status['long_position'] = 0
            if Source == 0:
                self.base_stock_data.to_csv(test_data_output_path + '//' + 'base_stock_data_with_metrics.csv',
                                            index=False)
            elif Source == 'GDrive':
                upload_base_stock_data_with_metrics(self.base_stock_data)
            elif Source == 'S3':
                Fetch_S3_Files().upload_base_stock_data_with_metrics(self.base_stock_data, 'base_stock_data_with_metrics')
        # else:
        elif (metric_value < max_close) and (prev_metric_value >= prev_max_close):
            self.entry_status['exist'] = 1
            self.entry_status['long_position'] = 1
            if Source == 0:
                self.base_stock_data.to_csv(test_data_output_path + '//' + 'base_stock_data_with_metrics.csv',
                                            index=False)
            elif Source == 'GDrive':
                upload_base_stock_data_with_metrics(self.base_stock_data)
            elif Source == 'S3':
                Fetch_S3_Files().upload_base_stock_data_with_metrics(self.base_stock_data, 'base_stock_data_with_metrics')

    # for supertrend
    # if metric_value >= max_close:
    #	self.entry_status['exist'] = 1
    #	self.entry_status['long_position'] = 0
    # else:
    #	self.entry_status['exist'] = 1
    #	self.entry_status['long_position'] = 1

    def take_entry(self):
        max_datetime = self.base_stock_data['datetime'].max()

        # try:
        # 	cur_option_price = list(self.option_stock_data[option_name][self.option_stock_data[option_name]['datetime']==max_datetime]['<close>'])[0]
        # except Exception as e:
        # 	print('exception raised while reading : ', e)
        # 	return

        print('cur entry time : ', max_datetime)
        if self.trade_status == 'closed':
            self.check_if_entry_exists()
            if self.entry_status['exist'] == 1:
                if self.entry_status['long_position'] == 1:
                    # take long entry
                    base_stock_entry_price = \
                    list(self.base_stock_data[self.base_stock_data['datetime'] == max_datetime]['<close>'])[0]
                    entry_datetime = max_datetime
                    # self.base_stock_data.to_csv(test_data_output_path + '//' + 'testing_base_stock_data.csv',
                    # 							index=False)
                    # self.option_stock_data[self._primary_pe_option_name].to_csv(test_data_output_path + '//' + 'testing_option_data.csv',
                    # 							index=False)

                    try:
                        entry_option_price = list(self.option_stock_data[self._primary_pe_option_name][
                                                      self.option_stock_data[self._primary_pe_option_name][
                                                          'datetime'] == max_datetime]['<close>'])[0]
                    except Exception as e:
                        print('exception raised while reading entry : ', e)
                        return

                    entry_option_name = self._primary_pe_option_name
                    entry_option_type = 'PE'
                    self.trade_status = 'open'
                    self.trade_type = 'long'
                    self.cur_trading_option = entry_option_name
                    self.option_entry_price = entry_option_price

                    self.stop_loss_price = entry_option_price + self.stop_loss_points
                    self.target_price = max(entry_option_price - self.target_points, 0)

                    sell_order_status = self.orderbook_obj._place_order_historical_data(variety='regular',
                                                                                        symb=entry_option_name,
                                                                                        exch='NFO', t_type='SELL',
                                                                                        qty=25, order_type='MARKET',
                                                                                        product='MIS',
                                                                                        price=entry_option_price,
                                                                                        trigger_price=0,
                                                                                        time_of_trade=entry_datetime,
                                                                                        comments='long')
                elif self.entry_status['long_position'] == 0:
                    # take long entry
                    base_stock_entry_price = \
                    list(self.base_stock_data[self.base_stock_data['datetime'] == max_datetime]['<close>'])[0]
                    entry_datetime = max_datetime
                    try:
                        entry_option_price = list(self.option_stock_data[self._primary_ce_option_name][
                                                      self.option_stock_data[self._primary_ce_option_name][
                                                          'datetime'] == max_datetime]['<close>'])[0]
                    except Exception as e:
                        print('exception raised while reading entry: ', e)
                        return
                    entry_option_name = self._primary_ce_option_name
                    entry_option_type = 'CE'
                    self.trade_status = 'open'
                    self.trade_type = 'short'
                    self.cur_trading_option = entry_option_name
                    self.option_entry_price = entry_option_price

                    self.stop_loss_price = entry_option_price + self.stop_loss_points
                    self.target_price = max(entry_option_price - self.target_points, 0)

                    sell_order_status = self.orderbook_obj._place_order_historical_data(variety='regular',
                                                                                        symb=entry_option_name,
                                                                                        exch='NFO', t_type='SELL',
                                                                                        qty=25, order_type='MARKET',
                                                                                        product='MIS',
                                                                                        price=entry_option_price,
                                                                                        trigger_price=0,
                                                                                        time_of_trade=entry_datetime,
                                                                                        comments='short')

    def check_if_exit_exist(self):
        max_datetime = self.base_stock_data['datetime'].max()
        option_name = self.cur_trading_option

        try:
            cur_option_price = list(
                self.option_stock_data[option_name][self.option_stock_data[option_name]['datetime'] == max_datetime][
                    '<close>'])[0]
        except Exception as e:
            print('exception raised while reading exit : ', e)
            return

        if cur_option_price > self.stop_loss_price:
            # exit the trade due to stop loss
            sell_order_status = self.orderbook_obj._place_order_historical_data(variety='regular', symb=option_name,
                                                                                exch='NFO', t_type='BUY', qty=25,
                                                                                order_type='MARKET', product='MIS',
                                                                                price=cur_option_price, trigger_price=0,
                                                                                time_of_trade=max_datetime,
                                                                                comments='stop loss hit')
            self.trade_status = 'closed'
            self.entry_status['exist'] = 0
            self.orderbook_obj.write_orderbook_data_to_disk()
            self.orderbook_obj = orderbookstorage('sma_trade_orderbook')
        elif cur_option_price < self.target_price:
            # exit the trade due to target hit
            sell_order_status = self.orderbook_obj._place_order_historical_data(variety='regular', symb=option_name,
                                                                                exch='NFO', t_type='BUY', qty=25,
                                                                                order_type='MARKET', product='MIS',
                                                                                price=cur_option_price, trigger_price=0,
                                                                                time_of_trade=max_datetime,
                                                                                comments='Target hit')
            self.trade_status = 'closed'
            self.entry_status['exist'] = 0
            self.orderbook_obj.write_orderbook_data_to_disk()
            self.orderbook_obj = orderbookstorage('sma_trade_orderbook')
        # write a condition to check if time in max_datetime is equal to 15:20:00, if so exit the trade
        elif max_datetime.hour == 14 and max_datetime.minute == 50:
            sell_order_status = self.orderbook_obj._place_order_historical_data(variety='regular', symb=option_name,
                                                                                exch='NFO', t_type='BUY', qty=25,
                                                                                order_type='MARKET', product='MIS',
                                                                                price=cur_option_price, trigger_price=0,
                                                                                time_of_trade=max_datetime,
                                                                                comments='EOD exit')
            self.trade_status = 'closed'
            self.entry_status['exist'] = 0
            self.orderbook_obj.write_orderbook_data_to_disk()
            self.orderbook_obj = orderbookstorage('sma_trade_orderbook')

        # trailing stop loss
        if cur_option_price < self.option_entry_price:
            new_stop_los = cur_option_price + self.stop_loss_points
            self.stop_loss_price = min(self.stop_loss_price, new_stop_los)

    def take_exit(self):
        max_datetime = self.base_stock_data['datetime'].max()

        if self.trade_status == 'open':
            self.check_if_exit_exist()

    def running_trade_algo(self):

        # create end_datetime as self.datetime_od_lookback with time=3:20:00
        end_datetime = self.datetime_of_algo_execution.replace(hour=15, minute=20, second=0)
        # create a loop from self.datetime_of_lookback to end_datetime by incrementing 1 minute
        cur_time = self.datetime_of_algo_execution
        # while(~(cur_time.hour==15 and cur_time.minute==21)):
        while (cur_time.hour != 15):
            self.add_new_incremental_data(cur_time, cur_time + datetime.timedelta(minutes=1))
            self.calculate_incremental_metrics()
            self.take_entry()
            self.take_exit()

            cur_time = cur_time + datetime.timedelta(minutes=1)


if __name__ == "__main__":
    import time
    start_time = time.time()
    # back_test_start_date = datetime.datetime(2022, 3, 8, 9, 30, 0)# when this day is a holiday it could cause issue because it would read previous day data only
    # back_test_start_date = datetime.datetime(2022, 5, 1, 9, 30, 0)
    # back_test_start_date = datetime.datetime(2022, 2, 2, 9, 30, 0)
    back_test_start_date = datetime.datetime(2022, 7, 20, 9, 30, 0)
    # back_test_start_date = datetime.datetime(2022, 3, 8, 9, 30, 0)
    # back_test_start_date = datetime.datetime(2022, 6, 29, 9, 30, 0)
    # back_test_start_date = datetime.datetime(2022, 4, 7, 9, 30, 0)
    # back_test_start_date = datetime.datetime(2022, 5, 21, 9, 30, 0)
    # back_test_start_date = datetime.datetime(2022, 5, 24, 9, 30, 0)
    # back_test_start_date = datetime.datetime(2022, 5, 25, 9, 30, 0)
    # back_test_end_date = datetime.datetime(2022, 2, 10, 9, 30, 0)
    # back_test_end_date = datetime.datetime(2022, 7, 20, 9, 30, 0)
    back_test_end_date = datetime.datetime(2022, 7, 20, 9, 31, 0)

    # data_interface_obj = trade_algo_structure('BANKNIFTY', back_test_start_date).running_trade_algo()
    # exit(0)
    skip_days = ['13-03-2020', '23-03-2020', '13-10-2020', '03-11-2020', '24-02-2021', '07-03-2022', '28-06-2022']
    # Convert skip_days to datetime objects
    skip_dates = [datetime.datetime.strptime(date_str, '%d-%m-%Y') for date_str in skip_days]
    import connect_with_drive
    if Source == 'GDrive':
        connect_with_drive.Gdrive()
    # create a loop from start_date to end_date by incrementing one day
    option_pattern_location = 'SQL'
    cur_date = back_test_start_date
    option_parameter = None
    while (cur_date <= back_test_end_date):
        if cur_date.date() not in [d.date() for d in skip_dates]:
            if option_parameter == None:
                option_parameter = option_parameters().fetch_pattern_for_option_selection(option_pattern_location)
                if option_parameter == None:
                    print("No option parameter to fetch!")
                    break
            
            data_interface_obj = trade_algo_structure('BANKNIFTY', cur_date, option_parameter).running_trade_algo()
                
        cur_date = cur_date + datetime.timedelta(days=1)

    if option_parameter != None:
        option_parameters().update_option_parameter_status(option_pattern_location, option_parameter)
        print("--- %s seconds ---" % (time.time() - start_time))
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
