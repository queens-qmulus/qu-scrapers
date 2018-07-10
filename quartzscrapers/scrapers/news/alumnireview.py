"""
quartzscrapers.scrapers.news.alumnireview
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the AlumniReview class scraper for parsing news data.
"""

from .gazette import Gazette


class AlumniReview(Gazette):
    """Scraper for Queen's Alumni Review news source.

    Site is currently located at <https://www.queensu.ca/gazette/stories/all>.
    """

    slug = 'alumnireview'

    @staticmethod
    def scrape(deep=False, location='./dumps/news'):
        """Scrape information custom to Queen's Alumni Review.

        This is a subcategory under Queen's Gazette.
        """
        super(AlumniReview, AlumniReview).scrape(
            deep, location, 'gazette/alumnireview/stories', AlumniReview.slug)
