import pandas as pd
import ta    # Python TA Lib
import pandas_ta as pta    # Pandas TA Libv

class SMA_Metrics_TA():
	def __init__(self, period):
		#self.df = df
		self.metric_status_col = 'SMA_calculated'
		self.metric_name = 'SMA_value'
		self.close_column_name = '<close>'
		self.period=period

	def calculate_metrics(self, df):
		#df = self.df
		#period = self.period
		df[self.metric_name] = ta.trend.SMAIndicator(df[self.close_column_name], self.period).sma_indicator()
		
		return df



	#def calculate_sma_incremental(self, df, period):

if __name__== '__main__':
	#inp_data = pd.read_csv(r'C:\Users\mdevaray\Documents\self\stock_market_project\Git_repos\pykiteconnect_repo\temp_data\stock_data.csv')

	sma = SMA_Metrics_TA(30)

	#inp_data = sma.calculate_metrics(inp_data)

	#write inp data to disk
	#inp_data.to_csv(r'C:\Users\mdevaray\Documents\self\stock_market_project\Git_repos\pykiteconnect_repo\temp_data\stock_data_sma.csv', index=False)

