import requests

class EarningsCall:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://financialmodelingprep.com/api/v3'

    def get_transcripts(self, symbol):
        url = f'{self.base_url}/historical-price-full/{symbol}?apikey={self.api_key}'
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def get_guidance(self, symbol):
        url = f'{self.base_url}/guidance/{symbol}?apikey={self.api_key}'
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None

# Example usage:
# api = EarningsCall('your_api_key_here')
# transcripts = api.get_transcripts('AAPL')
# guidance = api.get_guidance('AAPL')