import finnhub
import time
import os
import json
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CACHE_DIR = 'cache'

def get_cache_path(symbol):
    """Determines the cache file path for a given symbol."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{symbol}.json")

def is_cache_valid(path, ttl_minutes):
    """Checks if the cache file is still valid based on a TTL in minutes."""
    if not os.path.exists(path):
        return False
    file_mod_time = datetime.fromtimestamp(os.path.getmtime(path))
    return (datetime.now() - file_mod_time) < timedelta(minutes=ttl_minutes)

def fetch_stock_data(symbol, api_key, ttl_minutes):
    """Fetches stock data for a symbol using Finnhub, with caching."""
    cache_path = get_cache_path(symbol)
    
    if is_cache_valid(cache_path, ttl_minutes):
        logging.info(f"Loading {symbol} data from cache.")
        with open(cache_path, 'r') as f:
            return json.load(f)

    logging.info(f"Fetching {symbol} data from Finnhub API.")
    
    try:
        finnhub_client = finnhub.Client(api_key=api_key)
        quote = finnhub_client.quote(symbol)
        
        if 'c' not in quote or quote['c'] == 0:
            logging.warning(f"No current price data for {symbol} from Finnhub. Response: {quote}")
            return None

        transformed_data = {
            "Global Quote": {
                "01. symbol": symbol,
                "05. price": str(quote['c'])
            }
        }

        with open(cache_path, 'w') as f:
            json.dump(transformed_data, f)
            
        return transformed_data

    except Exception as e:
        logging.error(f"Failed to fetch data for {symbol} from Finnhub: {e}")
        return None

def fetch_all_symbols(config):
    """Fetches data for all symbols listed in the config using Finnhub."""
    api_key = config['finnhub']['api_key']
    symbols = config.get('symbols', [])
    cache_config = config.get('cache', {})
    ttl_minutes = cache_config.get('ttl_minutes', 29) # Default to 29 minutes
    rate_limit_delay = 1  # 60 calls/min rate limit, so 1 sec delay is safe
    all_data = {}

    for symbol in symbols:
        data = fetch_stock_data(symbol, api_key, ttl_minutes)
        if data:
            all_data[symbol] = data
        time.sleep(rate_limit_delay)

    return all_data
