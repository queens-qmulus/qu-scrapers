"""
quartzscrapers.scrapers.test_scraper.test_scraper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains an example scraper that is also used in tests.
Data from this scraper is not used in the API service.
"""

from ..utils import Scraper


class TestScraper:
    """An example scraper that scrapes Hacker News. HN was chosen
    since their front page is simple and their markup rarely changes.
    """

    scraper_key = 'test_scraper'
    location = './dumps/{}'.format(scraper_key)
    host = 'https://news.ycombinator.com'
    scraper = Scraper()
    logger = scraper.logger

    @staticmethod
    def scrape(location=location):
        """Scrape frontpage titles to JSON files.

        Args:
            location (optional): String location of output files.
        """
        TestScraper.logger.info('Starting test scrape')

        frontpage_soup = TestScraper._get_front_page()
        try:
            a_elem_list = frontpage_soup.select('.athing .title .storylink')
            TestScraper.logger.debug('%s items(s) found', len(a_elem_list))

            titles_list = TestScraper._get_titles(a_elem_list)

            TestScraper.logger.debug('Writing data dump')
            filename = 'test_scraper_data'
            TestScraper.scraper.write_data(titles_list, filename, location)
            TestScraper.logger.info('Completed Test scrape')

        except Exception:
            TestScraper.scraper.handle_error()

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
