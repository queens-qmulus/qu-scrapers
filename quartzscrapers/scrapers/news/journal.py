"""
quartzscrapers.scrapers.news.journal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the Journal class scraper for parsing news data.
"""

import re
from urllib.parse import urljoin

import pendulum

from ..utils import Scraper
from .news_helpers import get_urls_on_depth, get_article_page, save_article


class Journal:
    """Scraper for Queen's Journal news source.

    Site is currently located at <https://www.queensjournal.ca>.
    """

    host = 'http://www.queensjournal.ca'
    slug = 'queensjournal'
    scraper = Scraper()
    logger = scraper.logger

    @staticmethod
    def scrape(deep=False, location='./dumps/news'):
        """Scrape information custom to The Queen's Journal.

        Args:
            deep: Bool for a scrape of just the curent year, or every archive.
            location (optional): String location of output files.
        """
        Journal.logger.info('Starting Journal scrape')

        # QJ divides articles by archive year
        year_rel_urls = get_urls_on_depth(
            Journal._get_archive_years(), Journal.logger, deep)

        # Crawl each archived year
        for year_rel_url in year_rel_urls:
            Journal.logger.debug('ARCHIVE: %s', year_rel_url)

            try:
                # get number of pages a particular archive year needs to crawl
                # along with soup reference to continue page crawl
                num_pages = Journal._get_num_pages(year_rel_url)

                Journal.logger.debug('Total Pages: %s', num_pages)

                # Crawl each page for each year
                for page_index in range(num_pages):
                    Journal.logger.debug('Page %s', page_index + 1)

                    try:
                        article_rel_urls = Journal._get_article_rel_urls(
                            year_rel_url, page_index
                        )

                        # Scrape each article on a page
                        for article_rel_url in article_rel_urls:
                            try:
                                article_page, article_url = get_article_page(
                                    Journal.scraper,
                                    Journal.host,
                                    Journal.logger,
                                    article_rel_url,
                                )

                                article_data = (
                                    Journal._parse_article_data(
                                        article_page, article_url
                                    )
                                )

                                if article_data:
                                    save_article(
                                        Journal.scraper,
                                        article_data,
                                        location
                                    )

                                Journal.scraper.wait()
                            except Exception:
                                Journal.scraper.handle_error()

                    except Exception:
                        Journal.scraper.handle_error()

            except Exception:
                Journal.scraper.handle_error()

        Journal.logger.info('Completed Journal scrape')

    @staticmethod
    def _get_archive_years():
        # Get list of relative archive year URLs.

        # If a deep scrape is initiated, scraper will scrape every single
        # archive years (every possible thing to scrape). Otherwise, it
        # scrapes just the latest year.

        host_url = urljoin(Journal.host, 'news')
        soup = Journal.scraper.http_request(host_url)

        year_urls = soup.find('ul', 'views-summary').find_all('li')
        year_rel_urls = [url.find('a')['href'] for url in year_urls]

        return year_rel_urls

    @staticmethod
    def _get_num_pages(relative_url):
        # Request archive year URL and parse number of pages to crawl.

        year_url = urljoin(Journal.host, relative_url)
        soup = Journal.scraper.http_request(year_url)

        last_page = soup.find('li', 'pager-last')
        page_url = last_page.find('a')['href'] if last_page else 'page=0'

        # get last two digits from url of last page, i.e;
        # '/story/archive/news/2012/?page=13' results in 13
        index = page_url.rfind('=')
        num_pages = int(page_url[(index + 1):]) + 1  # +1 to go from 0 to n

        return num_pages

    @staticmethod
    def _get_article_rel_urls(relative_url, page_index):
        # Gets list of relative URLs for articles. Queen's Journal displays
        # 20 articles per page.

        year_url = urljoin(Journal.host, relative_url)
        soup = Journal.scraper.http_request(
            year_url, params=dict(page=page_index))

        articles = soup.find_all('div', 'node-story')
        article_rel_urls = (
            [article.find('h2').find('a')['href'] for article in articles]
            )

        return article_rel_urls

    @staticmethod
    def _parse_article_data(article_page, article_url):
        updated_iso = None
        regex_str = 'Last Updated: '

        title = article_page.find('div', id='content').find('h1').text.strip()

        # Find publish date and convert to ISO time standard.
        # Note: Pendulum added breaking changes from 1.5.x to 2.0.0. parse
        # function must be set to strict=False to prevent error
        published = article_page.find('li', 'date').text.strip()
        published_iso = pendulum.parse(published, strict=False).isoformat()

        # Find updated date if it exists and convert to ISO time standard.
        # NOTE: queensjournal.ca unofficially adds updated time via a
        # bolded sentence within article stating 'Last Updated:' with the
        # date. Use regex to find this tag
        updated_raw = article_page.find(text=re.compile(regex_str))

        if updated_raw:
            updated = updated_raw.strip()[len(regex_str):]
            updated_iso = pendulum.parse(updated, strict=False).isoformat()

        updated_iso = updated_iso or published_iso

        authors_raw = article_page.find('li', 'authors')
        authors = authors_raw.text.strip().split(', ') if authors_raw else []
        content = article_page.find('div', 'field-name-body').text.strip()
        content_raw = str(article_page.find('div', 'field-name-body'))

        data = {
            'title': title,
            'slug': Journal.slug,
            'url': article_url[:-1],
            'published': published_iso,
            'updated': updated_iso,
            'authors': authors,
            'content': content,
            'content_raw': content_raw,
            }

        return data
