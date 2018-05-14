from urllib.parse import urljoin

from ..utils import Scraper
from .journal import JournalScraper
    # GazetteScraper,
    # AlumniReviewScraper,
    # SmithMagazineScraper,
    # JurisDictionScraper,
    # )

class News:
    '''
    Scraper superclass for Queen's news articles.

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
        # GazetteScraper,
        # AlumniReviewScraper,
        # SmithMagazineScraper,
        # JurisDictionScraper,
        ]

    @staticmethod
    def scrape():
        '''Update database records for news scraper'''

        for news_source in news_sources:
            news_source.scrape()


