import pandas as pd
import ta    # Python TA Lib
import numpy as np
import pandas_ta as pta    # Pandas TA Libv

class Custom_1_Metrics_TA():
	def __init__(self, period):
		#self.df = df
		self.metric_status_col = 'custom_1_calculated'
		self.metric_name = 'custom_1_value'
		self.close_column_name = '<close>'
		self.period=period
		self._small_window_sma = 80
		self._large_window_sma = 120
		self._rsi_window = 14
		self._rsi_metric_name = 'rsi_14'

	def calculate_metrics(self, df):
		#df = self.df
		#period = self.period
		#df[self.metric_name] = ta.trend.SMAIndicator(df[self.close_column_name], self.period).sma_indicator()

		df['sma_40'] = ta.trend.SMAIndicator(df[self.close_column_name], self._small_window_sma).sma_indicator()
		df['sma_80'] = ta.trend.SMAIndicator(df[self.close_column_name], self._large_window_sma).sma_indicator()

		window = self._rsi_window
		col_name_rsi = self.metric_name + "_" + str(window)

		df = df.reset_index(drop=True)
		df['ser_no'] = df.index

		if 'prev_close' in df.columns:
			df = df.drop(columns=['prev_close'])


		df_prev_close = df.copy()
		df_prev_close['ser_no'] = df_prev_close['ser_no'] + 1
		df_prev_close = df_prev_close.rename(columns={self.close_column_name: 'prev_close'})

		print('rsi : shape before merge: ', df.shape)
		arg_data = df.merge(df_prev_close[['ser_no', 'prev_close']], how='left', on='ser_no')
		arg_data['prev_close'] = np.where(arg_data['prev_close'].isna(), arg_data[self.close_column_name],
										  arg_data['prev_close'])
		print('rsi : shape after merge: ', arg_data.shape)
		arg_data['gain_postv'] = np.where(arg_data[self.close_column_name] > arg_data['prev_close'],
										  arg_data[self.close_column_name] - arg_data['prev_close'], 0)
		arg_data['loss_postv'] = np.where(arg_data[self.close_column_name] < arg_data['prev_close'],
										  arg_data['prev_close'] - arg_data[self.close_column_name], 0)

		arg_data['rolling_gain_postv'] = arg_data.gain_postv.rolling(window + 1).sum()
		arg_data['rolling_loss_postv'] = arg_data.loss_postv.rolling(window + 1).sum()

		arg_data['rolling_gain_postv'] = arg_data['rolling_gain_postv'] - arg_data['gain_postv']
		arg_data['rolling_loss_postv'] = arg_data['rolling_loss_postv'] - arg_data['loss_postv']

		arg_data['rs_current'] = ((arg_data['rolling_gain_postv'] / 14) * 13 + arg_data[
			'gain_postv']) / ((arg_data['rolling_loss_postv'] / 14) * 13 + arg_data['loss_postv'])
		arg_data[self._rsi_metric_name] = 100 - (100 / (1 + arg_data['rs_current']))

		sel_cols = ['rsi_14']
		if 'rsi_14_prev' in arg_data.columns:
			arg_data = arg_data.drop(columns=['rsi_14_prev'])

		arg_data = arg_data.join(arg_data[sel_cols].shift(1).add_suffix('_prev'))

		# if rsi_14 is crossing below 30 then entry_flag = 1
		arg_data['custom_metric_1_rsi'] = arg_data.apply(
			lambda x: 1 if x['rsi_14'] < 30 and x['rsi_14_prev'] > 30 else 0, axis=1)
		# if rsi_14 is crossing above 70 then entry_flag = -1
		arg_data['custom_metric_1_rsi'] = arg_data.apply(
			lambda x: -1 if x['rsi_14'] > 70 and x['rsi_14_prev'] < 70 else x['custom_metric_1_rsi'], axis=1)

		# if sma_40 has crossed the sma_80 from below, then entry_flag = 1
		arg_data[self.metric_name] = arg_data.apply(
			lambda x: 1 if ((x['sma_40'] > x['sma_80']) and (x['custom_metric_1_rsi'] == 1)) else 0, axis=1)

		# if sma_40 has crossed the sma_80 from above, then entry_flag = -1
		arg_data[self.metric_name] = arg_data.apply(
			lambda x: -1 if ((x['sma_40'] < x['sma_80']) and (x['custom_metric_1_rsi'] == -1)) else x[
				self.metric_name], axis=1)

		return arg_data



	#def calculate_sma_incremental(self, df, period):

if __name__== '__main__':
	#inp_data = pd.read_csv(r'C:\Users\mdevaray\Documents\self\stock_market_project\Git_repos\pykiteconnect_repo\temp_data\stock_data.csv')

	sma = SMA_Metrics_TA(30)

	#inp_data = sma.calculate_metrics(inp_data)

	#write inp data to disk
	#inp_data.to_csv(r'C:\Users\mdevaray\Documents\self\stock_market_project\Git_repos\pykiteconnect_repo\temp_data\stock_data_sma.csv', index=False)

