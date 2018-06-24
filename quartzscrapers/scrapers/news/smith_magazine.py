import pendulum
from urllib.parse import urljoin

from ..utils import Scraper
from .news_helpers import get_urls_on_depth, get_article_page, save_article


class SmithMagazine:
    '''
    Scraper for Smith Magazine news source.
    '''

    host = 'https://smith.queensu.ca'
    slug = 'smithmagazine'
    scraper = Scraper()
    logger = scraper.logger

    @staticmethod
    def scrape(deep=False, location='./dumps/news'):
        '''
        Parse information custom to Smith Magazine.
        '''

        SmithMagazine.logger.info('Starting SmithMagazine scrape')

        try:
            magazine_issue_rel_urls = get_urls_on_depth(
                SmithMagazine._get_magazine_issues(),
                SmithMagazine.logger,
                deep
            )

            for magazine_issue_rel_url in magazine_issue_rel_urls:
                SmithMagazine.logger.debug('ARCHIVE: {url}'.format(url=magazine_issue_rel_url))

                try:
                    article_sections = SmithMagazine._get_article_sections(
                            magazine_issue_rel_url)

                    for article_section in article_sections:
                        title = article_section.find('h2', 'block-title').text.strip()

                        SmithMagazine.logger.debug('Article Section: {section}'.format(section=title))

                        article_rel_urls = SmithMagazine._get_article_rel_urls(
                            article_section)

                        for article_rel_url in article_rel_urls:
                            try:
                                article_page, article_url = get_article_page(
                                    SmithMagazine.scraper,
                                    SmithMagazine.host,
                                    SmithMagazine.logger,
                                    article_rel_url
                                )

                                article_data = SmithMagazine._parse_article_data(
                                    article_page, article_url)

                                if article_data:
                                    save_article(
                                        SmithMagazine.scraper,
                                        article_data,
                                        location
                                    )

                                SmithMagazine.scraper.wait()

                            except Exception as ex:
                                SmithMagazine.scraper.handle_error(ex, 'scrape')

                except Exception as ex:
                    SmithMagazine.scraper.handle_error(ex, 'scrape')

        except Exception as ex:
            SmithMagazine.scraper.handle_error(ex, 'scrape')

        SmithMagazine.logger.info('Completed SmithMagazine scrape')

    @staticmethod
    def _get_magazine_issues():
        '''
        Request URL for all archived magazine issues.

        Returns:
            List[String]
        '''

        magazine_archive_url = urljoin(SmithMagazine.host, 'magazine/archive')
        soup = SmithMagazine.scraper.http_request(magazine_archive_url)

        magazine_archives = soup.find_all('div', 'field-content')
        magazine_archive_urls = (
            [archive.find('a')['href'] for archive in magazine_archives]
            )

        return magazine_archive_urls

    @staticmethod
    def _get_article_sections(relative_url):
        '''
        Request magazine URL and parse BeautifulSoup HTML tag of each magazine
        section. Each magazine has varying article sections, such as
        'Features', 'Profiles', etc. Each section lists a series of article
        links.

        Returns:
            List[bs4.element.Tag]
        '''

        issue_url = urljoin(SmithMagazine.host, relative_url)
        soup =  SmithMagazine.scraper.http_request(issue_url)

        article_sections = (
            soup.find('div', 'group-right').find_all('div', 'field')
            )

        return article_sections

    @staticmethod
    def _get_article_rel_urls(article_section):
        '''
        Extract article relative URL from BeautifulSoup HTML tag.

        Returns:
            String
        '''
        articles = article_section.find_all('span', 'field-content')
        article_rel_urls = [article.find('a')['href'] for article in articles]

        return article_rel_urls

    @staticmethod
    def _parse_article_data(article_page, article_url):
        '''
        Parse data from article page tags

        Returns:
            Object
        '''

        title = article_page.find('div', 'field-name-title').text.strip()

        # Smith Magazine only shows issue season and year (Winter 217)
        # For the sake of news consistency, parse ISO only for the year.
        # It will always say  January 1st, with the respective year
        published = (article_page.find('div', 'field-name-field-issue')
                                 .find('div', 'field-item').text.strip())
        published_iso = pendulum.parse(published[-4:]).isoformat()

        authors_raw = article_page.find('div', 'field-name-field-author')
        authors = (
            authors_raw.find('div', 'field-item').text.strip().split(', ')
            if authors_raw else []
            )

        content_raw = article_page.find('div', 'field-name-body')
        content = content_raw.text.strip() if content_raw else ''

        data = {
            'title': title,
            'slug': SmithMagazine.slug,
            'url': article_url,
            'published': published_iso,
            'updated': published_iso,
            'authors': authors,
            'content': content,
            'content_raw': str(content_raw),
            }

        return data
