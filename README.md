# Crypto Price Tracker API & Analysis

A Python-based ecosystem featuring a Flask RESTful API and Jupyter Notebooks for tracking and analyzing cryptocurrency prices (Bitcoin, Ethereum) via the CoinGecko API.

## Overview

This project provides both an programmatic interface (Flask API) and an analytical environment (Jupyter Notebook) to retrieve, process, and visualize real-time and historical cryptocurrency market data.

## Features

- Flask REST API: Application factory pattern API serving market data endpoints.
- CoinGecko Integration: Reliable HTTP client interacting with the public CoinGecko API.
- Data Analysis: Exploratory Jupyter notebooks calculating technical indicators and price trends.
- Automated Testing: Pytest suite ensuring API reliability.

## Technology Stack

- Backend: Python 3, Flask
- Data Science: Pandas, JupyterLab
- Testing: Pytest

## Setup & Execution

1. Create and activate a virtual environment:
   `python -m venv venv`
2. Install dependencies:
   `pip install -r requirements.txt`
3. Run Flask API:
   `flask run`
4. Run Jupyter Notebooks:
   `jupyter notebook`
