import pytest
import requests
import json
import os
from src.fetcher import fetch_stock_data, get_cache_path

@pytest.fixture
def mock_config():
    return {
        'rate_limit': {'max_calls_per_min': 5}
    }

def test_fetch_stock_data_success(requests_mock, mock_config):
    symbol = 'AAPL'
    api_key = 'test_key'
    mock_url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}'
    mock_response = {
        "Time Series (Daily)": {
            "2025-07-03": {"4. close": "150.00"}
        }
    }
    requests_mock.get(mock_url, json=mock_response)

    data = fetch_stock_data(symbol, api_key, mock_config['rate_limit'])

    assert data is not None
    assert 'Time Series (Daily)' in data
    assert '2025-07-03' in data['Time Series (Daily)']

    # Check if cache was created
    cache_path = get_cache_path(symbol)
    assert os.path.exists(cache_path)
    with open(cache_path, 'r') as f:
        cached_data = json.load(f)
    assert cached_data == mock_response
    os.remove(cache_path) # clean up

def test_fetch_from_cache(mock_config):
    symbol = 'GOOG'
    api_key = 'test_key'
    cache_path = get_cache_path(symbol)
    mock_data = {"cached": True}
    with open(cache_path, 'w') as f:
        json.dump(mock_data, f)

    data = fetch_stock_data(symbol, api_key, mock_config['rate_limit'])
    assert data == mock_data
    os.remove(cache_path) # clean up

def test_fetch_stock_data_api_error(requests_mock, mock_config):
    symbol = 'MSFT'
    api_key = 'test_key'
    mock_url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}'
    requests_mock.get(mock_url, status_code=500)

    data = fetch_stock_data(symbol, api_key, mock_config['rate_limit'])
    assert data is None
