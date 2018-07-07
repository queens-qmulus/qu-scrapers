import os
import json
import time
import logging
import requests

import backoff
from bs4 import BeautifulSoup


class Scraper:
    '''Scraper base class. Handles common functions amongst all sub scrapers'''

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp, */*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch, br',
            'Accept-Language': 'en-US,en;q=0.8',
            'Cache-Control': 'no-cache',
            'dnt': '1',
            'Pragma': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
        }

    # Decorator for retrying HTTP requests. Using exponential backoff
    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_time=60)
    def http_request(
        self,
        url,
        params=None,
        cookies=None,
        headers=None,
        timeout=60,
        parse=True
    ):
        '''
        Requests given URL for HTML or BeautifulSoup response

        Returns:
            bs4.element.Tag             if parse=True
            requests.models.Response    otherwise
        '''

        response = self.session.get(
            url,
            params=params,
            cookies=cookies,
            headers=headers or self.headers,
            timeout=timeout,
        )

        # parse the response via BeautifulSoup after detecting its markup
        if parse:
            return self.soupify(response)

        return response

    def soupify(self, response):
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

    def write_data(self, data, filename, location='./dumps'):
        if not os.path.exists(location):
            os.makedirs(location)

        with open('{}/{}.json'.format(location, filename), 'w+') as file:
            file.write(json.dumps(data, indent=2, ensure_ascii=False))

    def update_data(self, data, subdata, key, filename, location='./dumps'):
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
            self.write_data(data, filename, location)

    def wait(self, seconds=2):
        '''Temporarily halt process for a certain period of time'''
        time.sleep(seconds)

    def handle_error(self, ex, func_name):
        '''Handle error by logging error message'''

        self.logger.error('Failure in {}'.format(func_name), exc_info=True)

