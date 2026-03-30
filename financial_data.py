import requests

class FinancialData:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://financialmodelingprep.com/api/v3/'

    def fetch_income_statement(self, ticker):
        url = f'{self.base_url}income-statement/{ticker}?apikey={self.api_key}'
        response = requests.get(url)
        return response.json()

    def fetch_balance_sheet(self, ticker):
        url = f'{self.base_url}balance-sheet-statement/{ticker}?apikey={self.api_key}'
        response = requests.get(url)
        return response.json()

    def fetch_cash_flow_statement(self, ticker):
        url = f'{self.base_url}cash-flow-statement/{ticker}?apikey={self.api_key}'
        response = requests.get(url)
        return response.json()