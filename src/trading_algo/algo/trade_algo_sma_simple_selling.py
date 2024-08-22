
from src.trading_algo.algo.trade_algo_structure import trade_algo_structure
from src.trading_algo.orderbook_storage.orderbook_storage_class import orderbookstorage

from src.trading_algo.metrics_calculation.sma_metrics_ta import SMA_Metrics_TA
from config import base_directory_project
from src.trading_algo.source import Source

from src.trading_algo.fetch_data_from_drive import upload_base_stock_data_with_metrics
from src.trading_algo.option_parameters_fetching import option_parameters
from src.trading_algo.fetch_data_from_S3 import Fetch_S3_Files
from datetime import timedelta

test_data_output_path = base_directory_project + "\\" + 'output_data'

class TradeAlgoSMAsimpleSelling(trade_algo_structure):
    def __init__(self,base_stock_name, datetime_of_algo_execution, pattern_for_option_selection):
        super().__init__(base_stock_name, datetime_of_algo_execution)

        self._pattern_for_option_selection_for_strategy = pattern_for_option_selection
        if pattern_for_option_selection == None:
            self._pattern_for_option_selection_for_strategy = [
                {'type': 'CE', 'sel_criteria': 'strike_price', 'itm_atm_otm': 'otm', 'delta_strike_price': -300,
                 'option_name': '', 'execution_strategy': {'simple_selling': {'short_action': 'SELL'}}},
                {'type': 'PE', 'sel_criteria': 'strike_price', 'itm_atm_otm': 'otm', 'delta_strike_price': -300,
                 'option_name': '', 'execution_strategy': {'simple_selling': {'long_action': 'SELL'}}}]
        self.selected_option_strategy = 'simple_selling'
        self.order_book_name = 'sma_trade_orderbook__sma_simple_selling_3'

    def initialise_metrics_obj(self):
        self.metrics_obj = SMA_Metrics_TA(200)
        self.metrics_col_name = 'SMA_value'

    # self.metrics_obj = Supertrend_Metrics_TA(10,3)
    # self.metrics_col_name = 'Supertrend_value'

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
            self.combined_stop_loss_points = 30
            self.combined_target_points = 400
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
                Fetch_S3_Files().upload_base_stock_data_with_metrics(self.base_stock_data,
                                                                     'base_stock_data_with_metrics')
            self.combined_stop_loss_points = 30
            self.combined_target_points = 400
        # else:
        #     self.entry_status['exist'] = 0

    # for supertrend
    # if metric_value >= max_close:
    #	self.entry_status['exist'] = 1
    #	self.entry_status['long_position'] = 0
    # else:
    #	self.entry_status['exist'] = 1
    #	self.entry_status['long_position'] = 1

    def update_running_trade(self):
        max_datetime = self.base_stock_data['datetime'].max()
        for option_to_update in self.option_execution_status_list:
            if option_to_update['trade_status'] == 'first_entry':
                option_to_update['stop_loss_points'] = self.stop_loss_points
                option_to_update['target_points'] = self.target_points
                option_to_update['trade_status'] = 'running'

                option_to_update['stop_loss_price'] = self.calc_stop_loss_price(option_to_update['entry_price'],
                                                                                option_to_update['entry_action'],
                                                                                option_to_update['stop_loss_points'])
                option_to_update['target_price'] = self.calc_target_price(option_to_update['entry_price'],
                                                                          option_to_update['entry_action'],
                                                                          option_to_update['target_points'])
            elif option_to_update['trade_status'] == 'running':
                # update stop loss or any other parameters
                # update the current price of all the options
                temp = 0
                # trailing stop loss
                try:
                    entry_option_price = list(self.option_stock_data[option_to_update['option_name']][
                                                  self.option_stock_data[option_to_update['option_name']][
                                                      'datetime'] == max_datetime]['<close>'])[0]
                except Exception as e:
                    print('exception raised while reading exit : ', e)
                    return

                option_to_update['cur_price'] = entry_option_price

                # trailing stop loss
                if option_to_update['entry_action'] == 'SELL':
                    if option_to_update['cur_price'] < option_to_update['entry_price']:
                        new_stop_loss = option_to_update['cur_price'] + option_to_update['stop_loss_points']
                        option_to_update['stop_loss_price'] = min(option_to_update['stop_loss_price'], new_stop_loss)
                elif option_to_update['entry_action'] == 'BUY':
                    if option_to_update['cur_price'] > option_to_update['entry_price']:
                        new_stop_loss = option_to_update['cur_price'] - option_to_update['stop_loss_points']
                        option_to_update['stop_loss_price'] = max(option_to_update['stop_loss_price'], new_stop_loss)
                else:
                    raise 'incorrect entry_action value'

    def evaluate_exit(self):
        max_datetime = self.base_stock_data['datetime'].max()

        for option_to_execute in self.option_execution_status_list:
            if option_to_execute['trade_status'] == 'running':
                if option_to_execute['entry_action'] == 'SELL':
                    if option_to_execute['cur_price'] > option_to_execute['stop_loss_price']:
                        option_to_execute['trade_status'] = 'exited'
                        self.place_exit_order(option_to_execute, max_datetime, 'stop loss hit')
                    elif option_to_execute['cur_price'] < option_to_execute['target_price']:
                        option_to_execute['trade_status'] = 'exited'
                        self.place_exit_order(option_to_execute, max_datetime, 'Target hit')
                    elif max_datetime.hour == 14 and max_datetime.minute == 50:
                        option_to_execute['trade_status'] = 'exited'
                        self.place_exit_order(option_to_execute, max_datetime, 'EOD exit')
                elif option_to_execute['entry_action'] == 'BUY':
                    if option_to_execute['cur_price'] < option_to_execute['stop_loss_price']:
                        option_to_execute['trade_status'] = 'exited'
                        self.place_exit_order(option_to_execute, max_datetime, 'stop loss hit')
                    elif option_to_execute['cur_price'] > option_to_execute['target_price']:
                        option_to_execute['trade_status'] = 'exited'
                        self.place_exit_order(option_to_execute, max_datetime, 'Target hit')
                    elif max_datetime.hour == 14 and max_datetime.minute == 50:
                        option_to_execute['trade_status'] = 'exited'
                        self.place_exit_order(option_to_execute, max_datetime, 'EOD exit')
                else:
                    raise 'incorrect entry_action value'

import datetime
if __name__=="__main__":
    import time
    #back_test_start_date = datetime.datetime(2022, 3, 8, 9, 30, 0)# when this day is a holiday it could cause issue because it would read previous day data only
    #back_test_start_date = datetime.datetime(2022, 5, 1, 9, 30, 0)
    #back_test_start_date = datetime.datetime(2022, 2, 2, 9, 30, 0)
    back_test_start_date = datetime.datetime(2022, 6, 29, 9, 30, 0)
    #back_test_start_date = datetime.datetime(2022, 7, 20, 9, 30, 0)
    #back_test_start_date = datetime.datetime(2022, 7, 25, 9, 30, 0)
    #back_test_start_date = datetime.datetime(2022, 3, 8, 9, 30, 0)
    #back_test_start_date = datetime.datetime(2022, 6, 29, 9, 30, 0)
    #back_test_start_date = datetime.datetime(2022, 4, 7, 9, 30, 0)
    #back_test_start_date = datetime.datetime(2022, 5, 21, 9, 30, 0)
    #back_test_start_date = datetime.datetime(2022, 5, 24, 9, 30, 0)
    #back_test_start_date = datetime.datetime(2022, 5, 25, 9, 30, 0)
    #back_test_end_date = datetime.datetime(2022, 2, 10, 9, 30, 0)
    back_test_end_date = datetime.datetime(2022, 7, 3, 9, 30, 0)
    #back_test_end_date = datetime.datetime(2022, 7, 20, 9, 30, 0)
    #back_test_end_date = datetime.datetime(2022, 7, 25, 9, 30, 0)
    #back_test_end_date = datetime.datetime(2022, 7, 30, 9, 30, 0)
    #back_test_end_date = datetime.datetime(2022, 7, 21, 9, 30, 0)

    # cur_date = back_test_start_date
    # while (cur_date <= back_test_end_date):
    #     print('running for the date : ', cur_date)
    #     data_interface_obj = TradeAlgoSMAsimpleSelling('BANKNIFTY', cur_date).running_trade_algo()
    #     cur_date = cur_date + datetime.timedelta(days=1)

    skip_days = ['13-03-2020', '23-03-2020', '13-10-2020', '03-11-2020', '24-02-2021', '07-03-2022', '28-06-2022']
    # Convert skip_days to datetime objects
    skip_dates = [datetime.datetime.strptime(date_str, '%d-%m-%Y') for date_str in skip_days]
    import connect_with_drive

    if Source == 'GDrive':
        connect_with_drive.Gdrive()
    # create a loop from start_date to end_date by incrementing one day
    option_pattern_location = 'SQL'
    #option_pattern_location = 'local'
    cur_date = back_test_start_date
    option_parameter = None

    # if option_parameter == None:
    #     option_parameter = option_parameters().fetch_pattern_for_option_selection(option_pattern_location)

    while (cur_date <= back_test_end_date):

        if cur_date.date() not in [d.date() for d in skip_dates]:


            data_interface_obj = TradeAlgoSMAsimpleSelling('BANKNIFTY', cur_date, option_parameter).running_trade_algo()
            #data_interface_obj = TradeAlgoSMAsimpleSelling('BANKNIFTY', cur_date, None).running_trade_algo()

        cur_date = cur_date + datetime.timedelta(days=1)

    # if option_parameter != None:
    #     option_parameters().update_option_parameter_status(option_pattern_location, option_parameter)
    #     print("--- %s seconds ---" % (time.time() - start_time))