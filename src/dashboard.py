import logging
import yaml
from flask import Flask, jsonify, request
from influxdb_client import InfluxDBClient

app = Flask(__name__)

def load_config():
    with open('config.yml', 'r') as f:
        return yaml.safe_load(f)

config = load_config()
influx_config = config['influxdb']

@app.route('/api/symbols')
def get_symbols():
    """Return the list of configured stock symbols."""
    return jsonify(config.get('symbols', []))

@app.route('/api/prices')
def get_prices():
    """Return historical price data for a given symbol from InfluxDB."""
    symbol = request.args.get('symbol')
    time_range = request.args.get('range', 'All') # Default to 'All'
    if not symbol:
        return jsonify({"error": "'symbol' parameter is required"}), 400
        
    # Map frontend range to InfluxDB duration
    range_map = {
        '1D': '-1d',
        '7D': '-7d',
        '1M': '-30d',
        '6M': '-180d', # approx 6 months
        '1Y': '-1y',
        'All': '0' # InfluxDB '0' means from the beginning of time
    }
    
    influx_range = range_map.get(time_range, '0') # Default to 'All' if range is invalid
    try:
        with InfluxDBClient(url=influx_config['url'], token=influx_config['token'], org=influx_config['org']) as client:
            query_api = client.query_api()
            query = f'''
            from(bucket: "{influx_config['bucket']}")
              |> range(start: -30d)
              |> filter(fn: (r) => r._measurement == "stock_price")
              |> filter(fn: (r) => r.symbol == "{symbol}")
              |> filter(fn: (r) => r._field == "price")
              |> yield(name: "mean")
            '''
            result = query_api.query(query)
            
            times = []
            prices = []
            for table in result:
                for record in table.records:
                    times.append(record.get_time())
                    prices.append(record.get_value())
            
            return jsonify({"times": times, "prices": prices})

    except Exception as e:
        logging.error(f"Error querying InfluxDB: {e}")
        return jsonify({"error": "Failed to retrieve data from database"}), 500
