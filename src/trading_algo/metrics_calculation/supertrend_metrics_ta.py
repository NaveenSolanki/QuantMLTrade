import pandas as pd
import ta    # Python TA Lib
import pandas_ta as pta    # Pandas TA Libv

class Supertrend_Metrics_TA():
	def __init__(self, period_1, period_2):
		#self.df = df
		self.metric_status_col = 'Supertrend_calculated'
		self.metric_name = 'Supertrend_value'
		self.close_column_name = '<close>'
		self.high_column_name = '<high>'
		self.low_column_name = '<low>'
		self.period_1=period_1
		self.period_2=period_2


	def calculate_metrics(self, df):
		#df = self.df
		#period = self.period
		#df[self.metric_name] = pta.supertrend(df[self.high_column_name], df[self.low_column_name], df[self.close_column_name], self.period_1, self.period_2)
		df[self.metric_name] = pta.supertrend(df[self.high_column_name], df[self.low_column_name], df[self.close_column_name], self.period_1, self.period_2).iloc[:,0]
		#if value.empty==False :
        #    value=value.iloc[-1][0]
        #    st=value
        #    print("st: ",st)
        #else:
        #    value='nan'
		
		return df



	#def calculate_sma_incremental(self, df, period):
		
if __name__== '__main__':
	inp_data = pd.read_csv(r'C:\Users\mdevaray\Documents\self\stock_market_project\Git_repos\pykiteconnect_repo\temp_data\stock_data.csv')

	sma = Supertrend_Metrics_TA(10,3)

	inp_data = sma.calculate_metrics(inp_data)

	#write inp data to disk
	inp_data.to_csv(r'C:\Users\mdevaray\Documents\self\stock_market_project\Git_repos\pykiteconnect_repo\temp_data\stock_data_supertrend.csv', index=False)

		

