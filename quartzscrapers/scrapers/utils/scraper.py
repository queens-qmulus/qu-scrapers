import os
import json
import time
import logging
import requests

from retrying import retry
from bs4 import BeautifulSoup


class Scraper:
    '''Scraper base class. Handles common functions amongst all sub scrapers'''

    logger = logging.getLogger(__name__)
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
    # @retry(wait_exponential_multiplier=1000, wait_exponential_max=30000)
    def http_request(url, params=None, cookies=None, headers=None, timeout=10000, parse=True): # TODO: Change timeout back to default
        '''
        Requests given URL for HTML or BeautifulSoup response

        Returns:
            bs4.element.Tag             if parse=True
            requests.models.Response    otherwise
        '''

        # TODO: Build in post requests into base scraper request function
        # Request 'search' page for list of courses.
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

        if type(data) == list:
            db[collection].insert_many(data)
        else:
            db[collection].insert(data)

        print('\nData saved\n')

    @staticmethod
    def write_data(data, filename, location='./dumps'):
        if not os.path.exists(location):
            os.makedirs(location)

        with open('{}/{}.json'.format(location, filename), 'w+') as file:
            file.write(json.dumps(data, indent=2, ensure_ascii=False))


    @staticmethod
    def update_data(data, subdata, key, filename, location='./dumps'):
        filepath = '{}/{}.json'.format(location, filename)

        if os.path.isfile(filepath):
            with open(filepath, 'r+t') as file:
                data_old = json.loads(file.read())
                data_old[key].append(subdata)

                # rewrite file from line 0
                file.seek(0)
                file.write(json.dumps(data_old, indent=2, ensure_ascii=False))
        else:
            data[key] = [subdata]
            Scraper.write_data(data, filename, location)

    @staticmethod
    def wait(seconds=2):
        '''Temporarily halt process for a certain period of time'''

        print('Waiting {seconds} seconds...\n'.format(seconds=seconds))
        time.sleep(seconds)

    @staticmethod
    def handle_error(ex, func_name):
        '''Handle error by logging error message'''

        Scraper.logger.error('Failure in {}'.format(func_name), exc_info=True)

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
        if 'xml' in content_type:
            return get_soup('lxml')

        # HTML markup
        else:
            return get_soup('html.parser')
