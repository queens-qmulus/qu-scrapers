"""
quartzscrapers.scrapers.utils.scraper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the base Scraper class, which handle generalized
functionality for all sup scrapers.
"""

import os
import json
import time
import logging
import requests

from enum import Enum

import backoff
from bs4 import BeautifulSoup


class ScrapeStatus(Enum):
    """TODO
    """
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'


class Scraper:
    """Scraper base class. Handle common functions amongst all sub scrapers."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.headers = {
            'Accept': ('text/html,application/xhtml+xml,application/xml;q=0.9,'
                       'image/webp, */*;q=0.8'),
            'Accept-Encoding': 'gzip, deflate, sdch, br',
            'Accept-Language': 'en-US,en;q=0.8',
            'Cache-Control': 'no-cache',
            'dnt': '1',
            'Pragma': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/63.0.3239.84 Safari/537.36'),
        }

    # Decorator for retrying HTTP requests. Using exponential backoff
    @backoff.on_exception(
        backoff.expo, requests.exceptions.RequestException, max_time=60)
    def http_request(
            self,
            url,
            params=None,
            cookies=None,
            headers=None,
            timeout=60,
            parse=True):
        """Handle HTTP request for a given URL.

        Request the given URL, and process as a BeautifulSoup object or as
        a requests response, depending on the result.

        Args:
            url: URL to request
            params (optional): Dictionary to be sent in the HTTP querystring.
            cookies (optional): Dict or CookieJar object.
            headers (optional): Dictionary of HTTP headers.
            timeout (optional): Time limit for request to complete.
            parse (optional): Bool to determine a BeautifulSoup parse result.

        Returns:
            BeautifulSoup element tag object if `parse` is true, else-wise a
            Requests response object.
        """

        response = self.session.get(
            url,
            params=params,
            cookies=cookies,
            headers=headers or self.headers,
            timeout=timeout,
        )

        # parse the response via BeautifulSoup after detecting its markup
        if parse:
            return self._soupify(response)

        return response

    def write_metadata(self, scrape_session_timestamp, scraper_key, status):
        """TODO
        """

        partial_metadata = {
            'scraper_key': scraper_key,
            'scrape_session_timestamp': scrape_session_timestamp,
            'status': status.value
        }

        location = './dumps/' + scrape_session_timestamp
        if not os.path.exists(location):
            os.makedirs(location)

        filepath = location + '/metadata.json'
        if os.path.isfile(filepath):
            with open(filepath, 'r+t') as file:
                content_dict = json.loads(file.read())
                content_dict[scraper_key] = partial_metadata

                # rewrite file from line 0
                file.seek(0)
                file.write(json.dumps(
                    content_dict, indent=2, ensure_ascii=False))
        else:
            with open(filepath, 'w+') as file:
                metadata = {}
                metadata[scraper_key] = partial_metadata
                metadata['scrape_session_timestamp'] = scrape_session_timestamp
                file.write(json.dumps(
                    metadata, indent=2, ensure_ascii=False))

    def write_data(self, data, filename, location='./dumps'):
        """Take data object and write to JSON file.

        Args:
            data: Dictionary of data.
            filename: String name of file.
            location (optional): String location of file.
        """
        if not os.path.exists(location):
            os.makedirs(location)

        with open('{}/{}.json'.format(location, filename), 'w+') as file:
            file.write(json.dumps(data, indent=2, ensure_ascii=False))

    def update_data(self, data, subdata, key, filename, location='./dumps'):
        """Update info by appending in existing file. Create if non-existent.

        Args:
            data: Dictionary of pre-existing data
            subdata: Dictionary of new data to append
            key: Dictionary key to locate data in file
            filename: String name of file
            location (optional): String location of file
        """
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
        """Temporarily halt process for a certain period of time.

        Args:
            seconds (optional): Number of seconds to pause operation.
        """
        time.sleep(seconds)

    def handle_error(self):
        """Handle error by logging error message."""
        self.logger.error('Scraper error', exc_info=True)

    def _soupify(self, response):
        """Detect response format and return respective BeautifulSoup parser.


        Detects if requests response format is HTML or XML, and returns a
        BeautifulSoup parser respective to response format.

        Args:
            response: Requests response object.

        Returns:
            BeautifulSoup element tag object.
        """

        content_type = response.headers.get('content-type', 'unknown')

        def get_soup(parser):
            """"Instantiate BeautifulSoup object"""
            return BeautifulSoup(response.text, parser)

        # XML markup
        if 'xml' in content_type:
            return get_soup('lxml')

        # HTML markup
        return get_soup('html.parser')
