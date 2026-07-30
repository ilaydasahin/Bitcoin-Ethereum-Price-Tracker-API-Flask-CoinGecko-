# Crypto Price Tracker API & Analysis

A Python-based ecosystem featuring a Flask RESTful API and a Jupyter Notebook for tracking and analyzing cryptocurrency prices (Bitcoin, Ethereum) via the CoinGecko API.

## Overview

This project provides both a programmatic interface (Flask API) and an analytical environment (Jupyter Notebook) to retrieve, process, and visualize real-time and historical cryptocurrency market data.

## Features

- **Flask REST API**: Application factory pattern API serving market data endpoints.
- **CoinGecko Integration**: Resilient HTTP client with retry/backoff (429/5xx) and a thread-safe TTL cache.
- **Centralized Error Handling**: Consistent JSON error responses; internal details are logged, never exposed to clients.
- **Input Validation**: `days`, `vs_currency` and coin id parameters are validated and return meaningful `400` errors.
- **Structured Logging**: Configurable log level per environment (`LOG_LEVEL`).
- **Data Analysis**: Exploratory Jupyter notebook for price visualization (candlestick charts, normalization) with Plotly.
- **Automated Testing**: Pytest suite covering routes, validation and error handling; runs in CI on every push.
- **Container Ready**: Dockerfile with gunicorn for production deployment.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info and endpoint index |
| GET | `/health` | Health check |
| GET | `/api/v1/prices?coins=bitcoin,ethereum&vs_currency=usd` | Current prices (max 10 coins) |
| GET | `/api/v1/coins/<coin_id>` | Coin market metadata |
| GET | `/api/v1/coins/<coin_id>/history?days=7&vs_currency=usd` | Historical prices (1-365 days) |
| GET | `/bitcoin`, `/ethereum`, `/bitcoin/info` | Legacy backward-compatible endpoints |

### Error Responses

All errors return a consistent JSON envelope:

```json
{ "status": "error", "message": "Parameter 'days' must be between 1 and 365" }
```

- `400` — invalid input (bad `days`, unsupported `vs_currency`, malformed coin id)
- `404` — unknown route or coin
- `502` / `503` — upstream (CoinGecko) failure or rate limit

## Technology Stack

- Backend: Python 3, Flask, gunicorn
- Data Science: Pandas, Plotly, Jupyter
- Testing: Pytest

## Setup & Execution

1. Create and activate a virtual environment:
   `python -m venv venv`
2. Install API dependencies:
   `pip install -r requirements.txt`
3. Run Flask API:
   `flask run` (or `python app.py`)
4. Run tests:
   `pytest`

### Jupyter Notebook (optional)

The analysis notebook requires extra packages that are not part of the API runtime:

```bash
pip install -r requirements-dev.txt
jupyter notebook notebooks/crypto_analysis.ipynb
```

### Docker

```bash
docker build -t crypto-tracker-api .
docker run -p 8000:8000 crypto-tracker-api
```

## Configuration

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `FLASK_ENV` | `development` | Config profile (`development`/`testing`/`production`) |
| `COINGECKO_BASE_URL` | CoinGecko v3 API | Upstream API base URL |
| `CACHE_DEFAULT_TIMEOUT` | `60` | TTL cache duration in seconds (0 disables) |
| `REQUEST_TIMEOUT` | `10` | Upstream request timeout in seconds |
| `LOG_LEVEL` | `INFO` (`DEBUG` in dev) | Logging verbosity |
