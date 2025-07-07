import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import './App.css';

function App() {
    const [symbols, setSymbols] = useState([]);
    const [selectedSymbol, setSelectedSymbol] = useState('');
    const [priceData, setPriceData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [timeRange, setTimeRange] = useState('All'); // New state for time range

    // Fetch the list of available symbols on component mount
    useEffect(() => {
        const fetchSymbolsWithRetry = (retries = 5, delay = 5000) => {
            axios.get('/api/symbols')
                .then(response => {
                    setSymbols(response.data);
                    if (response.data.length > 0) {
                        setSelectedSymbol(response.data[0]);
                    }
                    setError(''); // Clear any previous error
                })
                .catch(err => {
                    console.error(`Error fetching symbols (retries left: ${retries}):`, err);
                    if (retries > 0) {
                        setTimeout(() => fetchSymbolsWithRetry(retries - 1, delay), delay);
                    } else {
                        setError('Could not load stock symbols after multiple attempts.');
                    }
                });
        };

        fetchSymbolsWithRetry();
    }, []);

    // Fetch price data whenever the selected symbol or time range changes
    useEffect(() => {
        if (selectedSymbol) {
            setLoading(true);
            setError('');
            axios.get(`/api/prices?symbol=${selectedSymbol}&range=${timeRange}`) // Add range to API call
                .then(response => {
                    setPriceData(response.data);
                    setLoading(false);
                })
                .catch(err => {
                    console.error(`Error fetching price data for ${selectedSymbol}:`, err);
                    setError(`Could not load price data for ${selectedSymbol}.`);
                    setLoading(false);
                });
        }
    }, [selectedSymbol, timeRange]); // Add timeRange to dependency array

    const timeRanges = ['1D', '7D', '1M', '6M', '1Y', 'All'];

    return (
        <div className="App">
            <header className="App-header">
                <h1>Stock Price Tracker</h1>
            </header>
            <div className="controls">
                <label htmlFor="symbol-select">Select a Stock Symbol: </label>
                <select 
                    id="symbol-select"
                    value={selectedSymbol} 
                    onChange={e => setSelectedSymbol(e.target.value)}
                    disabled={symbols.length === 0}
                >
                    {symbols.map(symbol => (
                        <option key={symbol} value={symbol}>{symbol}</option>
                    ))}
                </select>
            </div>
            <div className="time-range-selector">
                {timeRanges.map(range => (
                    <button 
                        key={range} 
                        className={timeRange === range ? 'active' : ''}
                        onClick={() => setTimeRange(range)}
                    >
                        {range}
                    </button>
                ))}
            </div>
            <div className="chart-container">
                {loading && <p>Loading chart data...</p>}
                {error && <p className="error">{error}</p>}
                {!loading && !error && priceData && (
                    <Plot
                        data={[
                            {
                                x: priceData.times,
                                y: priceData.prices,
                                type: 'scatter',
                                mode: 'lines+markers',
                                marker: { color: '#1f77b4' },
                            },
                        ]}
                        layout={{
                            title: `Price History for ${selectedSymbol}`,
                            xaxis: { title: 'Time' },
                            yaxis: { title: 'Price (USD)' },
                        }}
                        useResizeHandler={true}
                        style={{ width: '100%', height: '100%' }}
                    />
                )}
            </div>
        </div>
    );
}

export default App;
