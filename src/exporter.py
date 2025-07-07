from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def export_to_influxdb(raw_data, config):
    """Write latest stock prices to InfluxDB."""
    influx_config = config['influxdb']
    token = influx_config.get('token')
    org = influx_config.get('org')
    bucket = influx_config.get('bucket')

    if not all([token, org, bucket]):
        logging.error("InfluxDB configuration is incomplete. Skipping export.")
        return

    try:
        with InfluxDBClient(url=influx_config['url'], token=token, org=org) as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            
            points = []
            for symbol, data in raw_data.items():
                if data and 'Global Quote' in data and '05. price' in data['Global Quote']:
                    try:
                        price = float(data['Global Quote']['05. price'])
                        point = Point("stock_price") \
                            .tag("symbol", symbol) \
                            .field("price", price) \
                            .time(datetime.utcnow())
                        points.append(point)
                    except (ValueError, TypeError) as e:
                        logging.warning(f"Could not parse price for {symbol}: {e}")
            
            if points:
                write_api.write(bucket=bucket, org=org, record=points)
                logging.info(f"Successfully wrote {len(points)} points to InfluxDB.")
            else:
                logging.warning("No valid price data found to write to InfluxDB.")

    except Exception as e:
        logging.error(f"Failed to write to InfluxDB: {e}")

def export_to_csv(processed_data, config):
    """Appends the processed data to a CSV file."""
    if processed_data.empty:
        logging.warning("No data to export to CSV.")
        return

    output_config = config.get('output', {})
    csv_path = output_config.get('csv_path', 'data/profit.csv')
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    try:
        # Create a summary row for the day
        summary_df = processed_data.groupby('date').agg({'total_worth': 'sum'}).reset_index()
        summary_df.rename(columns={'total_worth': 'daily_total_worth'}, inplace=True)

        if os.path.exists(csv_path):
            # Append without header
            summary_df.to_csv(csv_path, mode='a', header=False, index=False)
        else:
            # Write with header
            summary_df.to_csv(csv_path, mode='w', header=True, index=False)
        
        logging.info(f"Successfully appended daily summary to {csv_path}")
    except IOError as e:
        logging.error(f"Could not write to CSV file {csv_path}: {e}")
