import requests

from retrying import retry
from bs4 import BeautifulSoup
from pymongo import MongoClient


class Scraper:
    '''Scraper base class. Handles common functions amongst all sub scrapers'''

    session = requests.Session()
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp, */*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Accept-Language': 'en-US,en;q=0.8',
        'Cache-Control': 'no-cache',
        'dnt': '1',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
    }

    # Decorator for retrying behaviour for GET requests. Uses exponential
    # backoff by waiting 2 ^ (x * 1000) milliseconds between each retry, up to
    # 10 seconds, then 10 seconds afterwards
    @staticmethod
    @retry(wait_exponential_multiplier=1000, wait_exponential_max=10000)
    def get_url(url, params=None, cookies=None, headers=None, timeout=10):
        try:
            response = requests.get(
                url,
                params=params,
                cookies=cookies,
                headers=headers or Scraper.headers,
                timeout=timeout,
                )

            return BeautifulSoup(response.text, 'html.parser')
        except Exception as ex:
            print('Error in get_url():', ex.__class__.__name__)
            print('Error details:', ex)


    @staticmethod
    def save_data(data, collection):
        # TODO: Add env variables for Mongo credentials
        client = MongoClient('localhost', 27017)
        db = client['knowledge']

        db[collection].insert_many(data)
        print('\nData saved\n')

    @staticmethod
    def wait(seconds=2):
        print('Waiting {seconds} seconds...'.format(seconds=seconds))
        time.sleep(seconds)
