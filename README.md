# Stock-Price-Investment

A full-stack application to track real-time stock prices, featuring a Python backend, a React frontend, and InfluxDB for time-series data storage.

## Features

- **Decoupled Architecture**: A Python backend serving a JSON API and a separate React frontend.
- **Configurable**: Easily configure symbols, API keys, and output targets via `config.yml`.
- **Resilient**: Backend handles API rate limits with exponential backoff and caches data to avoid re-fetching.
- **Time-Series Database**: Uses InfluxDB to store historical price data efficiently.
- **Modern Frontend**: A responsive React dashboard with Plotly.js to visualize profit and loss over time.
- **Production-Ready**: Fully containerized with Docker and Docker Compose for easy setup and deployment. Includes a CI/CD pipeline with GitHub Actions.

## Quickstart

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/Stock-Price-Investment.git
    cd Stock-Price-Investment
    ```

2.  **Set up your environment:**

    Create a `.env` file in the root directory and add your Finnhub API key:
    ```
    FINNHUB_API_KEY=YOUR_API_KEY
    ```

3.  **Run with Docker Compose:**
    ```bash
    docker-compose up --build
    ```

## Important: API Rate Limits

The application uses the Finnhub API to fetch stock data. You will need a free API key from their website.

Each time the application's scheduled job runs, it makes one API request *per stock symbol* listed in your `config.yml`. To stay within the free limit, you must balance the number of symbols you track with the frequency of updates.

### Configuring the Update Frequency

The data fetch interval is configurable in `config.yml`. You can adjust the `interval_minutes` under the `scheduler` section. The default is set to 30 minutes, so the application will fetch new data every 30 minutes.

```yaml
scheduler:
  interval_minutes: 30 # Set how often to fetch new data
```

Be mindful of this limit when adding more symbols or decreasing the interval.

## Accessing the Services

-   **P&L Dashboard**: [http://localhost](http://localhost)
-   **InfluxDB UI**: [http://localhost:8086](http://localhost:8086)
-   **Grafana Dashboard**: [http://localhost:3000](http://localhost:3000)
