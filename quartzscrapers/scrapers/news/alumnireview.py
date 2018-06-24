import pendulum
from urllib.parse import urljoin

from .gazette import Gazette

class AlumniReview(Gazette):
    '''
    Scraper for Queen's Alumni Review news source.
    '''

    slug = 'alumnireview'

    @staticmethod
    def scrape(deep=False, location='./dumps/news'):
        '''
        Parse information custom to Queen's Alumni Review. This is a
        subcategory under Queen's Gazette.
        '''
        super(AlumniReview, AlumniReview).scrape(
            deep, location, 'gazette/alumnireview/stories', AlumniReview.slug)
