"""
quartzscrapers.scrapers.test_scraper.test_scraper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This module contains a scraper for the front page of hacker news.
It serves as a good example of a simple scraper and is used to test the
scraper and dataset scheduled task pipeline.
"""

import time

from ..utils import (Scraper, ScrapeStatus)

class TestScraper:
    """A scraper for hacker news."""

    scraper_key = "test_scraper"
    host = 'https://news.ycombinator.com'
    scraper = Scraper()
    logger = scraper.logger

    @staticmethod
    def scrape(scrape_session_timestamp, subfolder='test_scraper'):
        """Scrape frontpage titles to JSON files.

        Args:
            location (optional): String location output files.
        """
        TestScraper.logger.info('Starting test scrape')

        frontpage_soup = TestScraper._get_front_page()
        try:
            a_elem_list = frontpage_soup.select('.athing .title .storylink')
            TestScraper.logger.debug(
                '%s items(s) found', len(a_elem_list))

            titles_list = []
            for a_elem in a_elem_list:
                item = {
                    'title': a_elem.get_text(),
                    'link': a_elem.attrs['href']
                }
                titles_list.append(item)

            location = './dumps/' + scrape_session_timestamp + '/' + subfolder
            filename = 'test_scraper_data'
            TestScraper.logger.debug('Writing data dump')
            TestScraper.scraper.write_data(titles_list, filename, location)
            TestScraper.logger.debug('Writing TestScraper metadata')
            TestScraper.scraper.write_metadata(
                scrape_session_timestamp, TestScraper.scraper_key, ScrapeStatus.SUCCESS)
            TestScraper.logger.info('Completed Test scrape')

        except Exception:
            TestScraper.scraper.handle_error()
            TestScraper.scraper.write_metadata(
                scrape_session_timestamp, TestScraper.scraper_key, ScrapeStatus.FAILED)

    @staticmethod
    def _get_front_page():
        soup = TestScraper.scraper.http_request(TestScraper.host)
        return soup
