import pendulum
from urllib.parse import urljoin

from ..utils import Scraper

class SmithMagazineScraper:
    '''
    Scraper for Smith Magazine news source.
    '''

    host = 'https://smith.queensu.ca'
    slug = 'smithmagazine'

    @staticmethod
    def scrape(collection='articles'):
        '''
        Parse information custom to Smith Magazine.
        '''

        try:
            magazine_issue_rel_urls = SmithMagazineScraper.get_magazine_issues(
                'magazine/archive'
                )

            for magazine_issue_rel_url in magazine_issue_rel_urls:
                try:
                    print('ARCHIVE: {url}\n'.format(url=magazine_issue_rel_url))

                    article_sections = (
                        SmithMagazineScraper.get_article_sections(
                            magazine_issue_rel_url
                            ))

                    for article_section in article_sections[4:]:
                        import pdb; pdb.set_trace()

                        results = []

                        title = article_section.find('h2', 'block-title').text.strip()

                        article_rel_urls = SmithMagazineScraper.get_article_rel_urls(
                            article_section
                            )

                        print('Article Section: {section}'.format(section=title))
                        print('--------------------------------')

                        for article_rel_url in article_rel_urls:
                            try:
                                article_data = SmithMagazineScraper.parse_data(
                                    article_rel_url
                                    )

                                if article_data:
                                    results.append(article_data)

                                Scraper.wait()

                            except Exception as ex:
                                Scraper.handle_error(ex, 'scrape')

                        Scraper.save_data(results, collection)

                except Exception as ex:
                    Scraper.handle_error(ex, 'scrape')

        except Exception as ex:
            Scraper.handle_error(ex, 'scrape')


    @staticmethod
    def get_magazine_issues(relative_url):
        '''
        Request URL for all archived magazine issues.

        Returns:
            List[String]
        '''

        magazine_archive_url = urljoin(SmithMagazineScraper.host, relative_url)
        soup = Scraper.get_url(magazine_archive_url)

        magazine_archives = soup.find_all('div', 'field-content')
        magazine_archive_urls = (
            [archive.find('a')['href'] for archive in magazine_archives]
            )

        return magazine_archive_urls


    @staticmethod
    def get_article_sections(relative_url):
        '''
        Request magazine URL and parse BeautifulSoup HTML tag of each magazine
        section. Each magazine has varying article sections, such as
        'Features', 'Profiles', etc. Each section lists a series of article
        links.

        Returns:
            List[bs4.element.Tag]
        '''

        issue_url = urljoin(SmithMagazineScraper.host, relative_url)
        soup =  Scraper.get_url(issue_url)

        article_sections = (
            soup.find('div', 'group-right').find_all('div', 'field')
            )

        return article_sections


    @staticmethod
    def get_article_rel_urls(article_section):
        '''
        Extract article relative URL from BeautifulSoup HTML tag.

        Returns:
            String
        '''
        articles = article_section.find_all('span', 'field-content')
        article_rel_urls = [article.find('a')['href'] for article in articles]

        return article_rel_urls


    @staticmethod
    def parse_data(article_rel_url):
        '''
        Parse data from article page tags

        Returns:
            Object
        '''

        article_url = urljoin(SmithMagazineScraper.host, article_rel_url)
        soup = Scraper.get_url(article_url)

        print('Article: {url}'.format(url=article_url))

        title = soup.find('div', 'field-name-title').text.strip()

        # Smith Magazine only shows issue season and year (Winter 217)
        # For the sake of news consistency, parse ISO only for the year.
        # It will always say  January 1st, with the respective year
        published = (
            soup.find('div', 'field-name-field-issue')
                .find('div', 'field-item').text.strip()
            )
        published_iso = pendulum.parse(published[-4:]).isoformat()

        authors_raw = soup.find('div', 'field-name-field-author')
        authors = (
            authors_raw.find('div', 'field-item').text.strip().split(', ')
            if authors_raw else []
            )

        content = soup.find('div', 'field-name-body').text.strip()
        content_raw = str(soup.find('div', 'field-name-body'))

        data = {
            'title': title,
            'slug': SmithMagazineScraper.slug,
            'link': article_url,
            'published': published_iso,
            'updated': published_iso,
            'authors': authors,
            'content': content,
            'contentRaw': content_raw,
            }

        return data
