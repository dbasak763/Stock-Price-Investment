import requests
import time
import os
import json
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CACHE_DIR = 'cache'

def get_cache_path(symbol):
    """Determines the cache file path for a given symbol."""
    date_str = datetime.now().strftime('%Y-%m-%d')
    dir_path = os.path.join(CACHE_DIR, date_str)
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, f"{symbol}.json")

def is_cache_valid(path, ttl_days):
    """Checks if the cache file is still valid."""
    if not os.path.exists(path):
        return False
    file_mod_time = datetime.fromtimestamp(os.path.getmtime(path))
    return (datetime.now() - file_mod_time) < timedelta(days=ttl_days)

def fetch_stock_data(symbol, api_key, rate_limit_config):
    """Fetches stock data for a symbol, with caching and retries."""
    cache_path = get_cache_path(symbol)
    
    if is_cache_valid(cache_path, 1):
        logging.info(f"Loading {symbol} data from cache.")
        with open(cache_path, 'r') as f:
            return json.load(f)

    logging.info(f"Fetching {symbol} data from API.")
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}'
    
    max_retries = 3
    backoff_factor = 2
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

            # Check for Alpha Vantage specific error message
            data = response.json()
            if "Error Message" in data:
                logging.error(f"API returned an error for {symbol}: {data['Error Message']}")
                return None
            if "Information" in data:
                logging.warning(f"API call for {symbol} has an informational message: {data['Information']}")
                # This could indicate a rate limit warning, so we slow down.
                time.sleep(60 / rate_limit_config.get('max_calls_per_min', 5))

            if "Note" in data:
                logging.warning(f"API call for {symbol} has a note: {data['Note']}")
                # This could indicate a rate limit warning, so we slow down.
                time.sleep(60 / rate_limit_config.get('max_calls_per_min', 5))

            with open(cache_path, 'w') as f:
                json.dump(data, f)
            
            return data

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429 and attempt < max_retries - 1:
                sleep_time = backoff_factor ** attempt
                logging.warning(f"Rate limit hit for {symbol}. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logging.error(f"HTTP error fetching {symbol}: {e}")
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for {symbol}: {e}")
            return None
    
    return None

def fetch_all_symbols(config):
    """Fetches data for all symbols listed in the config."""
    api_key = config['api_key']
    symbols = config.get('symbols', [])
    rate_limit_config = config.get('rate_limit', {})
    all_data = {}

    for symbol in symbols:
        data = fetch_stock_data(symbol, api_key, rate_limit_config)
        if data:
            all_data[symbol] = data
        # Respect the API rate limit between different symbols
        time.sleep(60 / rate_limit_config.get('max_calls_per_min', 5))

    return all_data
