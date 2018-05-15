import time
from urllib.parse import urljoin

from ..utils import Scraper
from .journal import JournalScraper
from .gazette import GazetteScraper
from .alumnireview import AlumniReviewScraper
from .smith_magazine import SmithMagazineScraper
from .jurisdiction import JurisDictionScraper

class News:
    '''
    Scraper class for Queen's news articles.

    Queen's consists of several sources for news. As such, several subclasses
    exist to aggregate and normalize information into this superclass.

    Current sources include:

    Queen's Journal:        http://www.queensjournal.ca
    Queen's Gazette:        http://queensu.ca/gazette/stories/all
    Queen's Alumni Review:  http://queensu.ca/gazette/alumnireview/stories
    Smith Magazine:         https://smith.queensu.ca/magazine/archive
    Juris Diction:          http://www.juris-diction.ca
    '''

    news_sources = [
        JournalScraper,
        GazetteScraper,
        AlumniReviewScraper,
        SmithMagazineScraper,
        JurisDictionScraper,
        ]

    @staticmethod
    def scrape():
        '''Update database records for news scraper'''

        for news_source in News.news_sources:
            print('Starting {source} scraper'.format(source=news_source.slug))
            print('==================================\n')

            # TODO: Remove collection param when completed data validity of
            # all news scrapers

            start_time = time.time()
            news_source.scrape('articles_{slug}'.format(slug=news_source.slug))
            total_time = time.time() - start_time

            print('\nDone {source} scraper in {seconds} s\n'.format(
                source=news_source.slug, seconds=total_time))

        print('Completed news sources')
