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

        for news_source in News.news_sources:
            print('Starting {} scraper'.format(news_source.slug))
            print('==================================\n')

            news_source.scrape(deep=deep)

            print('\nDone {} scraper\n'.format(news_source.slug))

        print('Done all news scrapers')
