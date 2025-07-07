import os
import yaml
import logging
import time
from apscheduler.schedulers.background import BackgroundScheduler

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from gunicorn.app.base import BaseApplication

# Import project modules
from fetcher import fetch_all_symbols
from exporter import export_to_influxdb
from dashboard import app as flask_app

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_config():
    """Loads configuration from config.yml and environment variables."""
    try:
        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logging.error("config.yml not found. Please ensure it exists.")
        exit(1)

    # Override API key from environment variable if available
    api_key = os.getenv('FINNHUB_API_KEY')
    if api_key:
        if 'finnhub' not in config:
            config['finnhub'] = {}
        config['finnhub']['api_key'] = api_key

    # Validate that the API key is set
    finnhub_config = config.get('finnhub', {})
    if not finnhub_config.get('api_key') or 'YOUR_API_KEY' in str(finnhub_config.get('api_key')) or '${FINNHUB_API_KEY}' in str(finnhub_config.get('api_key')):
        logging.error("Finnhub API key not found or is invalid. Please set it in your .env file as FINNHUB_API_KEY=YOUR_KEY.")
        exit(1)
        
    return config

def run_job():
    """The main job to be run on a schedule."""
    logging.info("Starting scheduled job to fetch and store stock prices.")
    try:
        config = load_config()
        # 1. Fetch data from Finnhub
        raw_data = fetch_all_symbols(config)

        # 2. Export raw price data to InfluxDB
        export_to_influxdb(raw_data, config)

        logging.info("Scheduled job completed successfully.")
    except Exception as e:
        logging.error(f"An error occurred during the scheduled job: {e}", exc_info=True)

# Gunicorn application class
class StandaloneApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items() if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

def main():
    """Main entry point of the application."""
    config = load_config()
    
    # Schedule the job
    scheduler = BackgroundScheduler()
    # Get scheduler interval from config, with a safe default
    interval_hours = config.get('scheduler', {}).get('interval_minutes', 30)
    scheduler.add_job(run_job, 'interval', minutes=interval_minutes, misfire_grace_time=600)
    logging.info(f"Job scheduled to run every {interval_minutes} minutes.")
    scheduler.start()
    logging.info("Scheduler started. First job will run on start.")

    # Run the job immediately on startup
    run_job()

    # Use Gunicorn to serve the app
    port = config.get('server', {}).get('port', 8000)
    options = {
        'bind': f'0.0.0.0:{port}',
        'workers': 4,
    }
    logging.info(f"Starting web server on port {port}...")
    StandaloneApplication(flask_app, options).run()

if __name__ == '__main__':
    main()
