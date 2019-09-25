"""
quartzscrapers.scrapers.test_scraper.test_scraper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains a example scraper that is also used in tests.
Data from this scraper is not used in the API service.
"""

from ..utils import Scraper

class TestScraper:
    """An example scraper that scrapes Hacker News. HN was chosen
    since their front page is simple and their markup rarely changes.
    """

    scraper_key = "test_scraper"
    host = 'https://news.ycombinator.com'
    scraper = Scraper()
    logger = scraper.logger

    @staticmethod
    def scrape(scrape_session_timestamp):
        """Scrape frontpage titles to JSON files.

        Args:
            scrape_session_timestamp: Unix timestamp for current scrape session
        """
        TestScraper.logger.info('Starting test scrape')

        frontpage_soup = TestScraper._get_front_page()
        try:
            a_elem_list = frontpage_soup.select('.athing .title .storylink')
            TestScraper.logger.debug(
                '%s items(s) found', len(a_elem_list))

            titles_list = TestScraper._get_titles(a_elem_list)

            TestScraper.logger.debug('Writing data dump')
            location = './{}/{}/{}'.format(
                TestScraper.scraper.dump_location,
                scrape_session_timestamp,
                TestScraper.scraper_key)
            filename = 'test_scraper_data'
            TestScraper.scraper.write_data(titles_list, filename, location)

            TestScraper.logger.debug('Writing TestScraper metadata')
            TestScraper.scraper.write_metadata(
                scrape_session_timestamp,
                TestScraper.scraper_key,
                True)

            TestScraper.logger.info('Completed Test scrape')

        except Exception:
            TestScraper.scraper.handle_error()
            TestScraper.scraper.write_metadata(
                scrape_session_timestamp,
                TestScraper.scraper_key,
                True)

    @staticmethod
    def _get_front_page():
        soup = TestScraper.scraper.http_request(TestScraper.host)
        return soup

    @staticmethod
    def _get_titles(story_items):
        titles_list = []
        for a_elem in story_items:
            item = {
                'title': a_elem.get_text(),
                'link': a_elem.attrs['href']
            }
            titles_list.append(item)
        return titles_list
