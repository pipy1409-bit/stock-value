# Stock Value

## Overview
This repository provides a comprehensive tool for analyzing and valuing stock investments.

## Features
- Real-time stock price data via FMP API
- Various stock valuation methods implemented
- User-friendly CLI for interaction
- Detailed logging and reporting functionality

## Installation
To get started, clone the repository and install the required packages:

```bash
git clone https://github.com/pipy1409-bit/stock-value.git
cd stock-value
pip install -r requirements.txt
```

## Setup
After installation, you'll need to set up the FMP API key:
1. Visit [FMP API](https://fmpcloud.io/) and sign up for an API key.
2. Create a `.env` file in the root directory of the project with the following content:
   
   ```
   FMP_API_KEY=your_api_key_here
   ```

## Usage Examples
To run the application, use the following command:

```bash
python main.py --ticker AAPL
```

- Replace `AAPL` with any stock ticker symbol you want to analyze.

## Project Structure
```
stock-value/
├── main.py
├── valuation_methods.py
├── fmp_api.py
└── requirements.txt
```

## FMP API Integration Guide
The FMP API provides access to financial data for various stocks. Here’s a simple example of fetching the current price of a stock:

```python
import requests

def get_stock_price(ticker):
    url = f'https://fmpcloud.io/api/v3/quote/{ticker}?apikey={API_KEY}'
    response = requests.get(url)
    return response.json()[0]['price']
```

## Valuation Methods
Currently, the following valuation methods are implemented:
- Discounted Cash Flow (DCF)
- Price to Earnings Ratio (P/E)
- Net Asset Value (NAV)

## Disclaimer
This project is intended for educational purposes only. Use at your own risk. The author will not be responsible for any financial losses incurred while using this tool.