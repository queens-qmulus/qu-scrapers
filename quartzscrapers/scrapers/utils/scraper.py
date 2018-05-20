import time
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
    # 30 seconds, then 10 seconds afterwards
    @staticmethod
    @retry(wait_exponential_multiplier=1000, wait_exponential_max=30000)
    def http_request(url, params=None, cookies=None, headers=None, timeout=20, parse=True):
        '''
        Requests given URL for HTML or BeautifulSoup response

        Returns:
            bs4.element.Tag ||
        '''

        response = Scraper.session.get(
            url,
            params=params,
            cookies=cookies,
            headers=headers or Scraper.headers,
            timeout=timeout,
            )

        # parse the response via BeautifulSoup after detecting its markup
        if parse:
            return Scraper.soupify(response)

        return response


    @staticmethod
    def save_data(data, collection):
        '''Persists scraped data into database'''

        client = MongoClient('localhost', 27017)
        db = client['knowledge']

        db[collection].insert_many(data)
        print('\nData saved\n')

    @staticmethod
    def wait(seconds=2):
        '''Temporarily halt process for a certain period of time'''

        print('Waiting {seconds} seconds...\n'.format(seconds=seconds))
        time.sleep(seconds)


    @staticmethod
    def handle_error(ex, func_name):
        '''Handle error by logging error message'''

        print('{name} in {func_name}(): {ex}'.format(
            name=ex.__class__.__name__,
            func_name=func_name,
            ex=ex
            ))


    @staticmethod
    def soupify(response):
        '''
        Detect if requests response format is HTML or XML, and return a
        BeautifulSoup parser respective to response format.

        Returns:
            bs4.BeautifulSoup
        '''

        content_type = response.headers.get('content-type', 'unknown')

        def get_soup(parser):
            return BeautifulSoup(response.text, parser)

        # XML markup
        if 'xml' in response.headers.get('content-type', 'unknown'):
            return get_soup('lxml')

        # HTML markup
        else:
            return get_soup('html.parser')
