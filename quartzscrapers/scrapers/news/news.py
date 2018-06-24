from .journal import Journal
from .gazette import Gazette
from .alumnireview import AlumniReview
from .smith_magazine import SmithMagazine
from .jurisdiction import JurisDiction


class News:
    '''Scraper class for Queen's news articles.

    Queen's consists of several sources for news. As such, several subclasses
    exist to aggregate and normalize information into this superclass.

    Current sources include:

    Queen's Journal:        http://www.queensjournal.ca
    Queen's Gazette:        http://queensu.ca/gazette/stories/all
    Queen's Alumni Review:  http://queensu.ca/gazette/alumnireview/stories
    Smith Magazine:         https://smith.queensu.ca/magazine/archive
    Juris Diction:          http://www.juris-diction.ca
    '''

    logger = Scraper().logger

    news_sources = [
        Journal,
        Gazette,
        AlumniReview,
        SmithMagazine,
        JurisDiction,
    ]

    @staticmethod
    def scrape(deep=False):
        '''Update database records for news scraper'''

        News.logger.info('Starting News scrape')

        for news_source in News.news_sources:
            news_source.scrape(deep=deep)

        News.logger.info('Completed News scrape')
