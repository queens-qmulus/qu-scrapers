import pendulum
from urllib.parse import urljoin

from ..utils import Scraper

class JurisDictionScraper:
    '''
        Scraper for Juris Diction news source, Queen's Law Newspaper.
    '''

    host = 'http://www.juris-diction.ca'
    slug = 'jurisdiction'

    @staticmethod
    def scrape(collection='articles'):
        '''
        Parse information custom to Juris Diction.
        '''

        try:
            archive_month_urls = JurisDictionScraper.get_archive_month_urls()

            for archive_month_url in archive_month_urls:
                try:
                    print('ARCHIVE: {url}\n'.format(url=archive_month_url))

                    archive_page_urls = (
                        JurisDictionScraper.get_archive_page_urls(
                            archive_month_url
                        ))

                    page_num = 1

                    for archive_page_url in archive_page_urls:
                        results = []

                        try:
                            archive_page = Scraper.get_url(archive_page_url)

                            print('Page {page_num}'.format(page_num=page_num))
                            print('-------')

                            article_urls = (
                                JurisDictionScraper.get_rel_article_urls(
                                    archive_page
                                ))


                            for article_url in article_urls:
                                print('Article: {url}'.format(url=article_url))

                                try:
                                    article_data = (
                                        JurisDictionScraper.parse_data(
                                            article_url
                                        ))

                                    if article_data:
                                        results.append(article_data)

                                    Scraper.wait()

                                except Exception as ex:
                                    Scraper.handle_error(ex, 'scrape')

                            Scraper.save_data(results, collection)

                            page_num += 1

                        except Exception as ex:
                            Scraper.handle_error(ex, 'scrape')

                except Exception as ex:
                    Scraper.handle_error(ex, 'scrape')

        except Exception as ex:
            Scraper.handle_error(ex, 'scrape')


    @staticmethod
    def get_archive_month_urls():
        '''
        Request main URL and extract all archived month URLs.

        Returns:
            List[String]
        '''

        soup = Scraper.get_url(JurisDictionScraper.host)

        archives = soup.find('div', id='archives-3').find_all('li')
        archive_month_urls = [archive.find('a')['href'] for archive in archives]

        return archive_month_urls


    @staticmethod
    def get_archive_page_urls(archive_month_url):
        '''
        Requests an archive month's URL and crawls the archive for any
        additional paginated 'next' URLs, if they exist.

        Returns:
            List[String]
        '''

        archive_page_urls = [archive_month_url]

        archive_page = Scraper.get_url(archive_month_url)

        # paginate until we no longer see a 'next' button
        while archive_page.find('a', 'next'):
            archive_page_url = archive_page.find('a', 'next')['href']
            archive_page_urls.append(archive_page_url)

            archive_page = Scraper.get_url(archive_page_url)

        return archive_page_urls


    @staticmethod
    def get_rel_article_urls(archive_page):
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
    def parse_data(article_rel_url):
        '''
        Parse data from article page tags

        Returns:
            Object
        '''

        article_url = urljoin(JurisDictionScraper.host, article_rel_url)[:-1]
        soup = Scraper.get_url(article_url)

        title = soup.find('h1', 'entry-title').text.strip()

        # Queen's Juris Diction uses HTML5 element 'time', which already
        # contains ISO format in 'datetime' attribute
        published_iso = soup.find('time')['datetime']

        # Multiple authors are listed with commas, except for last author with
        # 'and' such as 'John, Alex and Jason'.
        authors_raw = soup.find('a', 'author-name')
        authors = (
            authors_raw.text.replace(' and', ',').split(', ')
            if authors_raw else []
            )

        content = soup.find('div', 'vw-post-content').text.strip()
        content_raw = str(soup.find('div', 'vw-post-content'))

        data = {
            'title': title,
            'slug': JurisDictionScraper.slug,
            'link': article_url,
            'published': published_iso,
            'updated': published_iso,
            'authors': authors,
            'content': content,
            'contentRaw': content_raw,
            }

        return data
