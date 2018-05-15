import re
import pendulum
from urllib.parse import urljoin

from ..utils import Scraper

class JournalScraper:
    '''
    Scraper for Queen's Journal news source.
    '''

    host = 'http://www.queensjournal.ca'
    slug = 'queensjournal'

    @staticmethod
    def scrape(collection='articles'):
        '''Parse information custom to The Queen's Journal'''

        # QJ divides articles by archive year
        year_rel_urls = JournalScraper.get_archive_years('news')

        # Series of try-catches here to ensure robustness of scraper despite
        # unavoidable errors per loop series

        # Crawl each archived year
        for year_rel_url in year_rel_urls:
            print('ARCHIVE: {url}'.format(url=year_rel_url))

            try:
                # get numberof pages a particular archive year needs to crawl
                # along with soup reference to continue page crawl
                num_pages = JournalScraper.get_num_pages(year_rel_url)

                print('Total Pages: {num_pages}'.format(num_pages=num_pages))
                print('===================================\n')

                # Crawl each page for each year
                for page_index in range(num_pages):
                    print('Page {page_num}'.format(page_num=(page_index + 1)))
                    print('---------')
                    results = []

                    try:
                        article_rel_urls = JournalScraper.get_article_rel_urls(
                            year_rel_url, page_index
                            )

                        # Scrape each article on a page
                        for article_rel_url in article_rel_urls:
                            try:
                                article_data = JournalScraper.parse_data(
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
    def get_archive_years(relative_url):
        '''
        Get list of relative archive year URLs.

        Returns:
            List[String]
        '''

        host_url = urljoin(JournalScraper.host, relative_url)
        soup = Scraper.get_url(host_url)

        year_urls = soup.find('ul', 'views-summary').find_all('li')
        year_rel_urls = [url.find('a')['href'] for url in year_urls]

        return year_rel_urls


    @staticmethod
    def get_num_pages(relative_url):
        '''
        Request archive year URL and parse number of pages to crawl

        Returns:
            Int
        '''

        year_url = urljoin(JournalScraper.host, relative_url)
        soup = Scraper.get_url(year_url)

        last_page = soup.find('li', 'pager-last')
        page_link = last_page.find('a')['href'] if last_page else 'page=0'

        # get last two digits from link of last page, i.e;
        # '/story/archive/news/2012/?page=13' results in 13
        index = page_link.rfind('=')
        num_pages = int(page_link[(index + 1):]) + 1 # +1 to go from 0 to n

        return num_pages

    @staticmethod
    def get_article_rel_urls(relative_url, page_index):
        '''
        Gets list of relative URLs for articles. Queen's Journal displays 20
        articles per page.

        Returns:
            List[String]
        '''
        year_url = urljoin(JournalScraper.host, relative_url)
        soup =  Scraper.get_url(year_url, params=dict(page=page_index))

        articles = soup.find_all('div', 'node-story')
        article_rel_urls = (
            [article.find('h2').find('a')['href'] for article in articles]
            )

        return article_rel_urls


    @staticmethod
    def parse_data(article_rel_url):
        '''
        Parse data from article page tags

        Returns:
            Object
        '''

        updated_iso = None
        regex_str = 'Last Updated: '

        article_url = urljoin(JournalScraper.host, article_rel_url)[:-1]
        soup = Scraper.get_url(article_url)

        print('Article: {url}'.format(url=article_url))

        title = soup.find('div', id='content').find('h1').text.strip()

        # Find publish date and convert to ISO time standard.
        # Note: Pendulum added breaking changes from 1.5.x to 2.0.0. parse
        # function must be set to strict=False to prevent error
        published = soup.find('li', 'date').text.strip()
        published_iso = pendulum.parse(published, strict=False).isoformat()

        # Find updated date if it exists and convert to ISO time standard.
        # NOTE: queensjournal.ca unofficially adds updated time via a
        # bolded sentence within article stating 'Last Updated:' with the
        # date. Use regex to find this tag
        updated_raw = soup.find(text=re.compile(regex_str))

        if updated_raw:
            updated = updated_raw.strip()[len(regex_str):]
            updated_iso = pendulum.parse(updated, strict=False).isoformat()

        authors_raw = soup.find('li', 'authors')
        authors = authors_raw.text.strip().split(', ') if authors_raw else []
        content = soup.find('div', 'field-name-body').text.strip()
        content_raw = str(soup.find('div', 'field-name-body'))

        data = {
            'title': title,
            'slug': JournalScraper.slug,
            'link': article_url,
            'published': published_iso,
            'updated': updated_iso,
            'authors': authors,
            'content': content,
            'contentRaw': content_raw,
            }

        return data
