import requests
import pandas as pd

# Alpha Vantage API key and endpoint
api_key = '9PK66JDA4OWZL96N'
symbols = ['DIS', 'GE', 'HD', 'TSLA']

def updateTotalDailyProfit(symbol, total_profit_daily, curr_stock_price):
    if symbol == "DIS":
        total_profit_daily += 28 * curr_stock_price
    elif symbol == "GE":
        total_profit_daily += 20 * curr_stock_price
    elif symbol == "HD":
        total_profit_daily += 7 * curr_stock_price
    elif symbol == "TSLA":
        total_profit_daily += 10 * curr_stock_price
    return total_profit_daily

total_profit_daily = 0.0
for symbol in symbols:
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        #print(data)

        #Extract daily stock prices (close prices)

        prices = {date: float(value['4. close']) for date, value in data['Time Series (Daily)'].items()}

        df = pd.DataFrame(list(prices.items()), columns=['Date', 'Close'])
        df['Date'] = pd.to_datetime(df['Date'])

        #Determine current stock price for company
        curr_stock_price = list(prices.items())[0][1]
        
        total_profit_daily = updateTotalDailyProfit(symbol, total_profit_daily, curr_stock_price)
        
        # Display the DataFrame
        print(f"Stock Prices for {symbol}: '\n'")
        print(df)
    else:
        print(f"Error in API request for {symbol}. Status code: {response.status_code}")
        continue
print("--------------'\n'")
print(f"Total Daily Profit: {total_profit_daily}")
