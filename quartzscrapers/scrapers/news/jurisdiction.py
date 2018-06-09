import pendulum
from urllib.parse import urljoin

from ..utils import Scraper
from .news_helpers import save_article, get_scrape_depth


class JurisDiction:
    '''
        Scraper for Juris Diction news source, Queen's Law Newspaper.
    '''

    host = 'http://www.juris-diction.ca'
    slug = 'jurisdiction'

    @staticmethod
    def scrape(deep=False, location='./dumps/news'):
        '''
        Parse information custom to Juris Diction.
        '''

        try:
            archive_month_urls = get_scrape_depth(
                JurisDiction._get_archive_month_urls(), deep)

            for archive_month_url in archive_month_urls:
                try:
                    print('ARCHIVE: {url}\n'.format(url=archive_month_url))

                    archive_page_urls = JurisDiction._get_archive_page_urls(
                        archive_month_url)

                    page_num = 1

                    for archive_page_url in archive_page_urls:
                        try:
                            archive_page = Scraper.http_request(archive_page_url)

                            print('Page {page_num}'.format(page_num=page_num))
                            print('-------')

                            article_rel_urls = JurisDiction._get_rel_article_urls(
                                archive_page)

                            for article_rel_url in article_rel_urls:
                                print('Article: {url}'.format(url=article_rel_url))

                                try:
                                    article_page, article_url = (
                                        JurisDiction._get_article_page(
                                            article_rel_url
                                        )
                                    )

                                    article_data = (
                                        JurisDiction._parse_news_data(
                                            article_page, article_url
                                        )
                                    )

                                    if article_data:
                                        save_article(article_data, location)

                                    Scraper.wait()

                                except Exception as ex:
                                    Scraper.handle_error(ex, 'scrape')

                            page_num += 1

                        except Exception as ex:
                            Scraper.handle_error(ex, 'scrape')

                except Exception as ex:
                    Scraper.handle_error(ex, 'scrape')

        except Exception as ex:
            Scraper.handle_error(ex, 'scrape')

    @staticmethod
    def _get_archive_month_urls():
        '''
        Request main URL and extract all archived month URLs.

        Returns:
            List[String]
        '''

        soup = Scraper.http_request(JurisDiction.host)

        archives = soup.find('div', id='archives-3').find_all('li')
        archive_month_urls = [arch.find('a')['href'] for arch in archives]

        return archive_month_urls

    @staticmethod
    def _get_archive_page_urls(archive_month_url):
        '''
        Requests an archive month's URL and crawls the archive for any
        additional paginated 'next' URLs, if they exist.

        Returns:
            List[String]
        '''

        archive_page_urls = [archive_month_url]

        archive_page = Scraper.http_request(archive_month_url)

        # paginate until we no longer see a 'next' button
        while archive_page.find('a', 'next'):
            archive_page_url = archive_page.find('a', 'next')['href']
            archive_page_urls.append(archive_page_url)

            archive_page = Scraper.http_request(archive_page_url)

        return archive_page_urls

    @staticmethod
    def _get_rel_article_urls(archive_page):
        '''
        Extract every article's relative URL from the current archive page.

        Returns:
            List[String]
        '''

        article_section = archive_page.find('div', 'vw-isotope')
        articles = article_section.find_all('h3', 'vw-post-box-title')

        article_rel_urls = [article.find('a')['href'] for article in articles]

        return article_rel_urls

    @staticmethod
    def _get_article_page(article_rel_url):
        article_url = urljoin(JurisDiction.host, article_rel_url)[:-1]
        article_page =  Scraper.http_request(article_url)

        return article_page, article_url

    @staticmethod
    def _parse_news_data(article_page, article_url):
        '''
        Parse data from article page tags

        Returns:
            Object
        '''

        title = article_page.find('h1', 'entry-title').text.strip()

        # Queen's Juris Diction uses HTML5 element 'time', which already
        # contains ISO format in 'datetime' attribute
        published_iso = article_page.find('time')['datetime']

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
            'url': article_url,
            'published': published_iso,
            'updated': published_iso,
            'authors': authors,
            'content': content,
            'content_raw': content_raw,
            }

        return data
