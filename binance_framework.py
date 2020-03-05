import pandas as pd
import time

from keys import keys
from binance.client import Client

client = Client(api_key=keys.apiKey, api_secret=keys.secretKey)


"""
The various columns provided by Binance
taken from:
https://python-binance.readthedocs.io/en/latest/binance.html#module-binance.client
"""
binance_columns = ['Open Time', 'Open', 'High', 'Low', 'Close',
            'Volume', 'Close Time', 'Quote asset volume', 
            'n_trades', 'Taker buy base asset volume', 
            'Taker buy quote asset volume', 'Ignore']



"""
The various time intervals provided by binance
"""
INTERVAL_1MINUTE = '1m'
INTERVAL_5MINUTE = '5m'
INTERVAL_15MINUTE = '15m'
INTERVAL_30MINUTE = '30m'
INTERVAL_1HOUR = '1h'




def get_data_by_intervals(n_iterations, currencies, interval):
    
    """
    get_data_by_intervals(
        n_iterations: Integer,
        currencies: list of currencies to download data,
        interval: interval of the timeframe (
            INTERVAL_1MIN,
            INTERVAL_5MIN,
            INTERVAL_15MIN,
            ...
        )
    )
    Description:
        DOWNLOADS DATA FROM BINANCE IN BATCHES OF 500 items.
        In total will return 500*n_rows - (n_rows+1) and
        no duplicate data should be present

    INPUTS:
        n_iterations: how many batches of 500 items to download
        
        currency: one of the varios currencies, examples: 
                    'BTCUSDT', 'LTCUSDT' ...etc
        interval:   Client.KLINE_INTERVAL_1MINUTE
                    Client.KLINE_INTERVAL_3MINUTE
                    Client.KLINE_INTERVAL_5MINUTE
                    Client.KLINE_INTERVAL_15MINUTE
                    Client.KLINE_INTERVAL_30MINUTE
                    Client.KLINE_INTERVAL_1HOUR
                    ...
    """
    #most recent timestamp to start downloading from
    starting_point = client.get_klines(symbol=currencies[0], 
                                  interval=interval, limit=1)[-1][0]
    
    main_df = pd.DataFrame()
    for currency in currencies:
        currency_cols = []
        for col in binance_columns:
            currency_cols.append(currency+' '+col)
        specific_currency_df = pd.DataFrame(columns=currency_cols)
        
        #downloading n iterations of a specific currency
        for i in range(0,n_iterations):
            #split in if elseto use starting_point
            if specific_currency_df.empty:
                new_data = client.get_klines(symbol=currency, 
                                              interval=interval,
                                              endTime = starting_point,
                                              limit=500
                                            )
            else:
                end_time = specific_currency_df[currency+' Open Time'].iloc[0]
                new_data = client.get_klines(symbol=currency, 
                                              interval=interval,
                                              endTime=end_time,
                                              limit=500
                                            )
            #merging all the rows of a specific currency in one DataFrame
            #we need to delete the first row of specific_currency_df or
            # delete the last row of new_data_df, it's repeated
            new_data_df = pd.DataFrame(new_data, columns=currency_cols)
            specific_currency_df = pd.concat([new_data_df,specific_currency_df[1:]],
                                             ignore_index=True)
            
        #merging the specific currency created into the main_df
        # were we keep all the data
        main_df = pd.concat([main_df, specific_currency_df],axis=1)
    return main_df




def show_time_skips(df, currencies):
    """
    show_time_skips(
        df = pandas.DataFrame object
        currencies = array of currencies, example: ['ETHUSDT','BTCUSDT' ]
    )

    Description:
        USED TO CHECK IF THERE ARE ANY SUDDEN JUMPS 
        IN THE TIMESTAMPS OF THE VARIOUS CURRENCIES
    """
    diff = 0
    df_len = len(df)
    for i in range(0,df_len-1):
        for currency in currencies:
            if i == 0:
                #get first time difference to compare with the rest
                diff = df[currency+' Close Time'].iloc[i+1] - df[
                    currency+' Close Time'].iloc[i]
                print('First time difference is: ',diff)
            if (df[currency+' Close Time'].iloc[i+1] - df[
                    currency+' Close Time'].iloc[i] != diff):
                print('\n')
                print(currency,'Time difference: ',(df[currency+' Close Time'
                                  ].iloc[i+1] - df[
                                      currency+' Close Time'].iloc[i]))
                print('starting at index: ',i)
                print('ending at index:   ', i+1)





def keep_one_timestamp(df, currencies):
    """
    keep_one_timestamp(
        df = pandas DataFrame object,
        currencies = list of currencies that are part of df
    )

    Description:
        removes repeated timestamps columns, keeping only the first's
        currencies Close Time and renaming it to 'Timestamp'
    """
    df['Timestamp'] = df[currencies[0]+' Close Time']
    for currency in currencies:
        df.drop([currency+' Open Time',
                 currency+' Close Time'],
                 axis=1, inplace=True)


def remove_ignore_columns(df, currencies):
    """
    Removes all the 'Ignore' columns in the DataFrame
    """
    for currency in currencies:
        df.drop(currency+' Ignore', axis=1, inplace=True)
