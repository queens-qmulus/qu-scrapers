"""
quartzscrapers.scrapers.news.jurisdiction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the JurisDiction class scraper for parsing news data.
"""

from collections import OrderedDict

from ..utils import Scraper
from .news_helpers import get_urls_on_depth, get_article_page, save_article


class JurisDiction:
    """Scraper for Juris Diction news source, Queen's Law Newspaper.

    Site is currently located at <http://juris-diction.ca>.
    """

    host = 'http://www.juris-diction.ca'
    slug = 'jurisdiction'
    scraper = Scraper()
    logger = scraper.logger

    @staticmethod
    def scrape(deep=False, location='./dumps/news'):
        """Scrape information custom to Juris Diction.

        Args:
            deep: Bool for a scrape of just the curent year, or every archive.
            location (optional): String location of output files.
        """
        JurisDiction.logger.info('Starting JurisDiction scrape')

        try:
            archive_month_urls = get_urls_on_depth(
                JurisDiction._get_archive_month_urls(),
                JurisDiction.logger,
                deep
            )

            for archive_month_url in archive_month_urls:
                try:
                    JurisDiction.logger.debug('ARCHIVE: %s', archive_month_url)

                    archive_page_urls = JurisDiction._get_archive_page_urls(
                        archive_month_url)

                    page_num = 1

                    for archive_page_url in archive_page_urls:
                        try:
                            archive_page = JurisDiction.scraper.http_request(
                                archive_page_url)

                            JurisDiction.logger.debug('Page %s', page_num)

                            article_rel_urls = (
                                JurisDiction._get_rel_article_urls(
                                    archive_page)
                            )

                            for article_rel_url in article_rel_urls:
                                try:
                                    article_page, article_url = (
                                        get_article_page(
                                            JurisDiction.scraper,
                                            JurisDiction.host,
                                            JurisDiction.logger,
                                            article_rel_url,
                                        )
                                    )

                                    article_data = (
                                        JurisDiction._parse_article_data(
                                            article_page, article_url)
                                    )

                                    if article_data:
                                        save_article(
                                            JurisDiction.scraper,
                                            article_data,
                                            location,
                                        )

                                    JurisDiction.scraper.wait()

                                except Exception:
                                    JurisDiction.scraper.handle_error()

                            page_num += 1

                        except Exception:
                            JurisDiction.scraper.handle_error()

                except Exception:
                    JurisDiction.scraper.handle_error()

        except Exception:
            JurisDiction.scraper.handle_error()

        JurisDiction.logger.info('Completed JurisDiction scrape')

    @staticmethod
    def _get_archive_month_urls():
        # Request main URL and extract all archived month URLs.

        soup = JurisDiction.scraper.http_request(JurisDiction.host)

        archives = soup.find('div', id='archives-3').find_all('li')
        archive_month_urls = [arch.find('a')['href'] for arch in archives]

        return archive_month_urls

    @staticmethod
    def _get_archive_page_urls(archive_month_url):
        # Requests an archive month's URL and crawls the archive for any
        # additional paginated 'next' URLs, if they exist.

        archive_page_urls = [archive_month_url]

        archive_page = JurisDiction.scraper.http_request(archive_month_url)

        # Paginate until we no longer see a 'next' button.
        while archive_page.find('a', 'next'):
            archive_page_url = archive_page.find('a', 'next')['href']
            archive_page_urls.append(archive_page_url)

            archive_page = JurisDiction.scraper.http_request(archive_page_url)

        return archive_page_urls

    @staticmethod
    def _get_rel_article_urls(archive_page):
        # Extract every article's relative URL from the current archive page.

        article_section = archive_page.find('div', 'vw-isotope')
        articles = article_section.find_all('h3', 'vw-post-box-title')

        article_rel_urls = [article.find('a')['href'] for article in articles]

        return article_rel_urls

    @staticmethod
    def _parse_article_data(article_page, article_url):
        title = article_page.find('h1', 'entry-title').text.strip()

        # Queen's Juris Diction uses HTML5 element 'time', which already
        # contains ISO format in 'datetime' attribute.
        published_iso = article_page.find(
            'div', class_='vw-post-meta-inner').find('time')['datetime']

        # Multiple authors are listed with commas, except for last author with
        # 'and' such as 'John, Alex and Jason'.
        authors_raw = article_page.find('a', 'author-name')
        authors = (
            authors_raw.text.replace(' and', ',').split(', ')
            if authors_raw else []
            )

        content = article_page.find('div', 'vw-post-content').text.strip()
        content_raw = str(article_page.find('div', 'vw-post-content'))

        data = {
            'title': title,
            'slug': JurisDiction.slug,
            'url': article_url[:-1],
            'published': published_iso,
            'updated': published_iso,
            'authors': authors,
            'content': content,
            'content_raw': content_raw,
        }

        return OrderedDict(data)
