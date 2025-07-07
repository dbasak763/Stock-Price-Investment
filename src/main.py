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
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if api_key:
        config['api_key'] = api_key
    elif 'api_key' not in config or config['api_key'] == 'YOUR_API_KEY':
        logging.error("API key not found. Please set it in config.yml or as ALPHA_VANTAGE_API_KEY env var.")
        exit(1)
        
    return config

def run_job():
    """The main job to be run on a schedule."""
    logging.info("Starting scheduled job to fetch and store stock prices.")
    try:
        config = load_config()
        # 1. Fetch data from Alpha Vantage
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
    interval_hours = config.get('scheduler', {}).get('interval_hours', 8)
    scheduler.add_job(run_job, 'interval', hours=interval_hours, misfire_grace_time=600)
    logging.info(f"Job scheduled to run every {interval_hours} hours.")
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
