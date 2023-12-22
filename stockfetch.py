import requests
from prometheus_client import start_http_server, Gauge
import time
from datetime import datetime, date

# Alpha Vantage API key and endpoint
api_key = '9PK66JDA4OWZL96N'
symbols = ['DIS', 'GE', 'HD', 'TSLA']

# Prometheus metric
total_daily_profit_metric = Gauge('total_daily_profit', 'Total daily profit for all symbols')

def updateTotalDailyProfit(symbol, total_profit_daily, curr_stock_price):
    if symbol == "DIS":
        amt = 28 * curr_stock_price
        print(f"Present worth of Disney's shares: {amt}")
        total_profit_daily += amt
    elif symbol == "GE":
        amt = 20 * curr_stock_price
        print(f"Present worth of General Electric shares: {amt}")
        total_profit_daily += amt
    elif symbol == "HD":
        amt = 7 * curr_stock_price
        print(f"Present worth of Home Depot shares: {amt}")
        total_profit_daily += amt
    elif symbol == "TSLA":
        amt = 10 * curr_stock_price
        print(f"Present worth of Tesla's shares: {amt}")
        total_profit_daily += amt
    return total_profit_daily

def scrape_data():
    total_profit_daily = 0.0

    # Load the last push date from a file
    try:
        with open("last_push_date.txt", "r") as file:
            last_push_date_str = file.read().strip()
            last_push_date = datetime.strptime(last_push_date_str, "%Y-%m-%d").date()
    except FileNotFoundError:
        last_push_date = None

    # Check if the metric has been pushed today
    if last_push_date is not None and last_push_date == date.today():
        print("Metric already pushed today. Skipping.")
        return

    for symbol in symbols:
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}'
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            latest_date = next(iter(data['Time Series (Daily)'].keys()))
            curr_stock_price = float(data['Time Series (Daily)'][latest_date]['4. close'])
            print(f"Current Stock Price For {symbol}: {curr_stock_price}")
            total_profit_daily = updateTotalDailyProfit(symbol, total_profit_daily, curr_stock_price)

        else:
            print(f"Error in API request for {symbol}. Status code: {response.status_code}")
            continue

    print("--------------'\n'")
    print(f"Total Daily Profit: {total_profit_daily}")

    # Update Prometheus metric
    total_daily_profit_metric.set(total_profit_daily)

    # Save the current date to the file
    with open("last_push_date.txt", "w") as file:
        file.write(str(date.today()))

if __name__ == '__main__':
    start_http_server(8000)
    scrape_data()
