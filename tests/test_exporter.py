import pytest
import pandas as pd
import os
from src.exporter import export_to_csv, export_to_prometheus
from prometheus_client import REGISTRY

@pytest.fixture
def mock_config():
    return {
        'output': {
            'csv_path': 'data/test_profit.csv'
        }
    }

@pytest.fixture
def processed_data():
    return pd.DataFrame([
        {'symbol': 'AAPL', 'shares': 10, 'latest_price': 150.0, 'total_worth': 1500.0, 'date': pd.to_datetime('2025-07-03')}
    ])

def test_export_to_csv(processed_data, mock_config):
    csv_path = mock_config['output']['csv_path']
    if os.path.exists(csv_path):
        os.remove(csv_path)

    export_to_csv(processed_data, mock_config)

    assert os.path.exists(csv_path)
    df = pd.read_csv(csv_path)
    assert len(df) == 1
    assert df['daily_total_worth'].iloc[0] == 1500.0
    os.remove(csv_path)

def test_export_to_prometheus(processed_data):
    export_to_prometheus(processed_data)

    assert REGISTRY.get_sample_value('stock_latest_price', {'symbol': 'AAPL'}) == 150.0
    assert REGISTRY.get_sample_value('stock_total_worth', {'symbol': 'AAPL'}) == 1500.0
    assert REGISTRY.get_sample_value('portfolio_total_worth') == 1500.0
