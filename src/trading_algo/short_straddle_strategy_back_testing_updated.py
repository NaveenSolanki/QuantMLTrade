#DISCLAIMER:
#1) This sample code is for learning purposes only.
#2) Always be very careful when dealing with codes in which you can place orders in your account.
#3) The actual results may or may not be similar to backtested results. The historical results do not guarantee any profits or losses in the future.
#4) You are responsible for any losses/profits that occur in your account in case you plan to take trades in your account.
#5) TFU and Aseem Singhal do not take any responsibility of you running these codes on your account and the corresponding profits and losses that might occur.
#6) The running of the code properly is dependent on a lot of factors such as internet, broker, what changes you have made, etc. So it is always better to keep checking the trades as technology error can come anytime.
#7) This is NOT a tip providing service/code.
#8) This is NOT a software. Its a tool that works as per the inputs given by you.
#9) Slippage is dependent on market conditions.
#10) Option trading and automatic API trading are subject to market risks

#from kiteconnect import KiteConnect
import datetime
import pandas as pd

#historical data fetching
#from trading_algo.unorganised_code.get_historical_data import historical_stock_fetcher
import time
import threading
import pandas as pd
import requests


#historical data fetching
#from trading_algo.unorganised_code.get_historical_data import historical_stock_fetcher
# from src.trading_algo.get_historical_data import historical_stock_fetcher

####################__INPUT__#####################
# api_key = ""
# access_token = ""
# kc = KiteConnect(api_key=api_key)
# kc.set_access_token(access_token)

#TIME TO FIND THE STRIKE
entryHour   = 0
entryMinute = 0
entrySecond = 0
startTime = datetime.time(entryHour, entryMinute, entrySecond)

stock="BANKNIFTY" # BANKNIFTY OR NIFTY
otm = 300  #If you put -100, that means its 100 points ITM.
SL_point = 40
PnL = 0
premium = 100
df = pd.DataFrame(columns=['Date','CE_Entry_Price','CE_Exit_Price','PE_Entry_Price','PE_Exit_Price','PnL'])
df["Date"] = [datetime.date.today()]

#Time
#Find NSE price . If nse price < yesterday closing (ATM)
#ENtry Price BUY
#Exit SL == target


expiry = {
    "year": "23",
    "month": "6",
    "day": "08",
    #YYMDD  22O06  22OCT  22OCT YYMMM
    #YYMMM  22, N, OV
    #YYMDD   22 o/n/d   03
    #YYMDD  22  6  10   22JUN
    #YYMDD 22D10  22NOV
}

clients = [
    {
        "broker": "zerodha",
        "userID": "",
        "apiKey": "",
        "accessToken": "",
        "qty" : 50
    }
]


##################################################


def findStrikePriceATM_backtesting(datetime_to_fetch, name):
    print(" Placing Orders ")
    global kc
    global clients
    global SL_percentage

    if stock == "BANKNIFTY":
        #name = "NSE:"+"NIFTY BANK"   #"NSE:NIFTY BANK"
        name = "banknifty"
    elif stock == "NIFTY":
        #name = "NSE:"+"NIFTY 50"       #"NSE:NIFTY 50"
        name = "nifty"
    #TO get feed to Nifty: "NSE:NIFTY 50" and banknifty: "NSE: NIFTY BANK"

    strikeList=[]

    prev_diff = 10000
    closest_Strike=10000


    #intExpiry=expiry["year"]+expiry["month"]+expiry["day"]   #22OCT

    ######################################################
    #FINDING ATM


    #create historical data object for spot price only
    #get only date part from datetime_to_fetch
    #date_parameter = datetime_to_fetch.date()
    # only_spot_price_object = historical_stock_fetcher('',datetime_to_fetch, name,get_only_spot=1)
    # ltp_for_spot = only_spot_price_object._get_data_for_spot_ticker_for_a_given_date(datetime_to_fetch)

    ltp_for_spot = data_interface_obj.get_ltp_spot(stock, datetime_to_fetch)

    if(ltp_for_spot==-1):
        print("Error in fetching data, probably a holiday")
        return 0

    if stock == "BANKNIFTY":
        closest_Strike = int(round((ltp_for_spot / 100),0) * 100)
        print(closest_Strike)


    elif stock == "NIFTY":
        closest_Strike = int(round((ltp_for_spot / 50),0) * 50)
        print(closest_Strike)

    print("closest",closest_Strike)
    closest_Strike_CE = closest_Strike+otm
    closest_Strike_PE = closest_Strike-otm

    #if stock == "BANKNIFTY":
    #    atmCE = "NFO:BANKNIFTY" + str(intExpiry)+str(closest_Strike_CE)+"CE"
    #    atmPE = "NFO:BANKNIFTY" + str(intExpiry)+str(closest_Strike_PE)+"PE"
    #elif stock == "NIFTY":
    #    atmCE = "NFO:NIFTY" + str(intExpiry)+str(closest_Strike_CE)+"CE"
    #    atmPE = "NFO:NIFTY" + str(intExpiry)+str(closest_Strike_PE)+"PE"


    from src.trading_algo.option_contract_naming.get_closest_expiry_contract import get_closest_expiry
    expiry_name_object = get_closest_expiry()
    next_closest_thursday = expiry_name_object.get_next_closest_weekly_expiry(datetime_to_fetch)
    atmCE = expiry_name_object.get_option_contract_name(stock, next_closest_thursday, closest_Strike_CE, 'CE')
    atmPE = expiry_name_object.get_option_contract_name(stock, next_closest_thursday, closest_Strike_PE, 'PE')

    print('atm ce ',atmCE)
    print('atm pe ',atmPE)

    takeEntry_backtesting(stock, closest_Strike_CE, closest_Strike_PE, atmCE, atmPE, datetime_to_fetch)


def takeEntry_backtesting(spot_name,closest_Strike_CE, closest_Strike_PE, atmCE, atmPE,datetime_to_fetch):
    global SL_point
    global PnL
    datetime_to_fetch = datetime_to_fetch.replace(hour=9, minute=30, second=0, microsecond=0)

    
    #write a try and exception block below
    try:
        # ce_option_data_object = historical_stock_fetcher(atmCE, datetime_to_fetch, spot_name)
        # ce_entry_price = ce_option_data_object._get_data_for_option_ticker_for_a_given_date(datetime_to_fetch)

        ce_entry_price = data_interface_obj.get_ltp_option(atmCE, datetime_to_fetch)

    #now write exception block for above to print the error and return None
    except Exception as e:
        print("Error in fetching data for CE ", e, ' ', datetime_to_fetch, ' ', atmCE)
        #exit(-2)
        return None

    try:
        # pe_option_data_object = historical_stock_fetcher(atmPE, datetime_to_fetch, spot_name)
        # pe_entry_price = pe_option_data_object._get_data_for_option_ticker_for_a_given_date(datetime_to_fetch)

        pe_entry_price = data_interface_obj.get_ltp_option(atmPE, datetime_to_fetch)

    except Exception as e:
        print("Error in fetching data for PE ", e, ' ', datetime_to_fetch, ' ', atmPE)
        #exit(-2)
        return None
    #ce_entry_price = getLTP(atmCE)
    #pe_entry_price = getLTP(atmPE)
    PnL = ce_entry_price + pe_entry_price

    if pe_entry_price==-1 or ce_entry_price==-1:
        print("Error in fetching data for PE or CE -1 ", ' ', atmCE, ' ',atmPE,' ', datetime_to_fetch)
        return None

    print("Current PnL is: ", PnL)
    df['CE_Entry_Price'] = [ce_entry_price]
    df['PE_Entry_Price'] = [pe_entry_price]

    print(" closest_CE ATM ", closest_Strike_CE, " CE Entry Price = ", ce_entry_price)
    print(" closest_PE ATM", closest_Strike_PE, " PE Entry Price = ", pe_entry_price)

    ceSL = round(ce_entry_price + SL_point, 1)
    peSL = round(pe_entry_price + SL_point, 1)
    print("Placing Order CE Entry Price = ", ce_entry_price, "|  CE SL => ", ceSL)
    print("Placing Order PE Entry Price = ", pe_entry_price, "|  PE SL => ", peSL)


    sell_order_status = orderbook_obj._place_order_historical_data(variety = 'regular', symb = atmCE, exch = 'NFO', t_type = 'SELL', qty = 25, order_type = 'MARKET', product = 'MIS',price = ce_entry_price,trigger_price = 0,time_of_trade = datetime_to_fetch,comments = 'test comment')
    sell_order_status = orderbook_obj._place_order_historical_data(variety = 'regular', symb = atmPE, exch = 'NFO', t_type = 'SELL', qty = 25, order_type = 'MARKET', product = 'MIS',price = pe_entry_price,trigger_price = 0,time_of_trade = datetime_to_fetch,comments = 'test comment')


    traded = "No"

    #variable to be used to track date and update below variable
    #create a start time variable which has date as datetime_to_fetch and time as 9:15
    start_time = datetime_to_fetch.replace(hour=9, minute=31, second=0, microsecond=0)
    cur_time = start_time

    while traded == "No":# create a loop on time to go thorugh every minute
        #dt = datetime.datetime.now()

        try:
            #ltp = ce_option_data_object._get_data_for_option_ticker_for_a_given_date(cur_time)
            #ltp1 = pe_option_data_object._get_data_for_option_ticker_for_a_given_date(cur_time)
            ltp = data_interface_obj.get_ltp_option(atmCE, cur_time)
            ltp1 = data_interface_obj.get_ltp_option(atmPE, cur_time)
            if ((ltp > ceSL) or (cur_time.hour >= 15 and cur_time.minute >= 15)) and ltp != -1:
                #oidexitCE = placeOrderSingle( atmCE, "BUY", qty, "MARKET", ceSL, "regular")
                sell_order_status = orderbook_obj._place_order_historical_data(variety = 'regular', symb = atmCE, exch = 'NFO', t_type = 'BUY', qty = 25, order_type = 'MARKET', product = 'MIS',price = ltp, trigger_price = 0,time_of_trade = cur_time,comments = 'stop loss hit')
                PnL = PnL - ltp
                print("Current PnL is: ", PnL)
                df["CE_Exit_Price"] = [ltp]
                print("The OID of Exit CE is: ", sell_order_status)
                traded = "CE"
                cur_time = cur_time - datetime.timedelta(minutes=1)
            elif ((ltp1 > peSL) or (cur_time.hour >= 15 and cur_time.minute >= 15)) and ltp1 != -1:
                #oidexitPE = placeOrderSingle( atmPE, "BUY", qty, "MARKET", peSL, "regular")
                sell_order_status = orderbook_obj._place_order_historical_data(variety = 'regular', symb = atmPE, exch = 'NFO', t_type = 'BUY', qty = 25, order_type = 'MARKET', product = 'MIS',price = ltp1, trigger_price = 0,time_of_trade = cur_time,comments = 'stop loss hit')
                PnL = PnL - ltp1
                print("Current PnL is: ", PnL)
                df["PE_Exit_Price"] = [ltp1]
                print("The OID of Exit PE is: ", sell_order_status)
                traded = "PE"
                cur_time = cur_time - datetime.timedelta(minutes=1)
            else:
                temp = 0
                #print("NO SL is hit")
                #time.sleep(1)

        except:
            print("Couldn't find LTP , RETRYING !!")
            #time.sleep(1)

        #update cur_time to next minute
        cur_time = cur_time + datetime.timedelta(minutes=1)


    if (traded == "CE"):
        peSL = pe_entry_price
        while traded == "CE":
            #dt = datetime.datetime.now()
            dt = cur_time
            try:
                #ltp = getLTP(atmPE)
                #ltp = pe_option_data_object._get_data_for_option_ticker_for_a_given_date(dt)
                #ltp = data_interface_obj.get_ltp_option(atmCE, datetime_to_fetch)
                ltp = data_interface_obj.get_ltp_option(atmPE, dt)
                if ((ltp > peSL) or (dt.hour >= 15 and dt.minute >= 15)) and ltp != -1:
                    #oidexitPE = placeOrderSingle( atmPE, "BUY", qty, "MARKET", peSL, "regular")
                    sell_order_status = orderbook_obj._place_order_historical_data(variety = 'regular', symb = atmPE, exch = 'NFO', t_type = 'BUY', qty = 25, order_type = 'MARKET', product = 'MIS',price = ltp, trigger_price = 0,time_of_trade = dt,comments = 'stop loss hit')
                    PnL = PnL - ltp
                    print("Current PnL is: ", PnL)
                    df["PE_Exit_Price"] = [ltp]
                    print("The OID of Exit PE is: ", sell_order_status)
                    traded = "Close"
                else:
                    temp =0
                    #print("PE SL not hit")
                    #time.sleep(1)

            except:
                print("Couldn't find LTP , RETRYING !!")
                #time.sleep(1)

            cur_time = cur_time + datetime.timedelta(minutes=1)

    elif (traded == "PE"):
        ceSL = ce_entry_price
        while traded == "PE":
            #dt = datetime.datetime.now()
            dt = cur_time
            try:
                #ltp = getLTP(atmCE)
                #ltp = ce_option_data_object._get_data_for_option_ticker_for_a_given_date(dt)
                ltp = data_interface_obj.get_ltp_option(atmCE, dt)
                if ((ltp > ceSL) or (dt.hour >= 15 and dt.minute >= 15)) and ltp != -1:
                    #oidexitCE = placeOrderSingle( atmCE, "BUY", qty, "MARKET", ceSL, "regular")
                    sell_order_status = orderbook_obj._place_order_historical_data(variety = 'regular', symb = atmCE, exch = 'NFO', t_type = 'BUY', qty = 25, order_type = 'MARKET', product = 'MIS',price = ltp, trigger_price = 0,time_of_trade = dt,comments = 'stop loss hit')
                    PnL = PnL - ltp
                    df["CE_Exit_Price"] = [ltp]
                    print("Current PnL is: ", PnL)
                    print("The OID of Exit CE is: ", sell_order_status)
                    traded = "Close"
                else:
                    temp = 0
                    #print("CE SL not hit")
                    #time.sleep(1)
            except:
                print("Couldn't find LTP , RETRYING !!")
                #time.sleep(1)

            cur_time = cur_time + datetime.timedelta(minutes=1)

    elif (traded == "Close"):
        print("All trades done. Exiting Code")

    #exitPosition_backtesting(atmCE, ceSL, ce_entry_price, atmPE, peSL, pe_entry_price, qty)

hist_obj = None
#def getLTP_spot(instrument, datetime_to_fetch):


#checkTime_tofindStrike()
#datetime_to_fetch = datetime.datetime(2022, 7, 4, 10, 49, 0)
#findStrikePriceATM_backtesting(datetime_to_fetch, 'BANKNIFTY')

#from trading_algo.unorganised_code.data_interface_for_live_and_historical import DataInterfaceLiveAndHistorical
from src.trading_algo.data_interface_for_live_and_historical import DataInterfaceLiveAndHistorical
data_interface_obj = DataInterfaceLiveAndHistorical(live_data_fetch_flag=0)

#from trading_algo.unorganised_code.orderbook_storage_class import orderbookstorage
from src.trading_algo.orderbook_storage.orderbook_storage_class import orderbookstorage
orderbook_obj = orderbookstorage('short_straddle_orderbook')

#back_test_start_date = datetime.datetime(2017, 1, 1, 9, 30, 0)
#back_test_start_date = datetime.datetime(2020, 6, 7, 9, 30, 0)
back_test_start_date = datetime.datetime(2022, 7, 5, 9, 30, 0)
#back_test_start_date = datetime.datetime(2022, 1, 1, 9, 30, 0)
#back_test_end_date = datetime.datetime(2022, 8, 30, 9, 30, 0)
back_test_end_date = datetime.datetime(2022, 7, 15, 9, 30, 0)

# back_test_start_date = datetime.datetime(2017, 8, 1, 9, 30, 0)
# back_test_end_date = datetime.datetime(2017, 8, 2, 9, 30, 0)

#2022-04-01 09:30:00 #2017-08-01 09:30:00

#create import daterange statement
daterange = pd.date_range(start=back_test_start_date, end=back_test_end_date)

#create a loop from startdate to enddate by incrementing one day at a time
for dt in daterange:
    data_interface_obj = DataInterfaceLiveAndHistorical(live_data_fetch_flag=0)
    orderbook_obj = orderbookstorage('short_straddle_orderbook')
    print("running trades for : ", dt)





    #checkTime_tofindStrike()
    ##datetime_to_fetch = datetime.datetime(2022, 7, 4, 10, 49, 0)
    findStrikePriceATM_backtesting(dt, 'BANKNIFTY')
    #time.sleep(1)

    orderbook_obj.write_orderbook_data_to_disk()

#df["PnL"] = [PnL]
#df.to_csv('Str1_websocket.csv',mode='a',index=True,header=True)


#2022-03-23 09:30:00 date for which it is taking high run time