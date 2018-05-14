import pendulum
from urllib.parse import urljoin

# from .news import News
# from quartzscrapers.scrapers.news_temp.news import News
from ..utils import Scraper
from .helpers import add_default_fields


class GazetteScraper:
    '''
    Scraper for Queen's Gazette news source.
    '''

    host = 'http://www.queensu.ca'
    slug = 'gazette'

    @staticmethod
    def scrape(collection='articles'):
        '''Parse information custom to Queen's Gazette'''

        num_pages = GazetteScraper.get_num_pages('gazette/stories/all')

        print('Total Pages: {num_pages}'.format(num_pages=num_pages))
        print('===================================\n')

        for page_index in range(num_pages):
            print('Page {page_num}'.format(page_num=page_index))
            print('---------')
            results = []

            try:
                article_rel_urls = GazetteScraper.get_article_rel_urls(
                    'gazette/stories/all', page_index
                    )

                for article_rel_url in article_rel_urls:
                    try:
                        article_data = GazetteScraper.parse_data(
                            article_rel_url
                            )

                        if article_data:
                            results.append(
                                add_default_fields(article_data)
                                )

                        Scraper.wait()

                    except Exception as ex:
                        Scraper.handle_error(ex, 'scrape')

                Scraper.save_data(results, collection)

            except Exception as ex:
                Scraper.handle_error(ex, 'scrape')

    @staticmethod
    def get_num_pages(relative_url):
        '''
        Request URL for all archived articles and parse number of pages to
        crawl.

        Returns:
            Int
        '''

        stories_all_url = urljoin(GazetteScraper.host, relative_url)
        soup = Scraper.get_url(stories_all_url)

        page_link = soup.find('li', 'pager-last').find('a')['href']

        # get last two digits from link of last page, i.e;
        # '/story/archive/news/2012/?page=13' results in 13
        index = page_link.rfind('=')
        num_pages = int(page_link[(index + 1):]) + 1 # +1 to go from 0 to n

        return num_pages

    @staticmethod
    def get_article_rel_urls(relative_url, page_index):
        '''
        Gets list of relative URLs for articles. Queen's Gazette displays
        approximately 16 articles per page.

        Returns:
            List[String]
        '''

        article_url = urljoin(GazetteScraper.host, relative_url)
        soup =  Scraper.get_url(article_url, params=dict(page=page_index))

        articles = soup.find_all('div', 'story-title')
        article_rel_urls = [article.find('a')['href'] for article in articles]

        return article_rel_urls


    @staticmethod
    def parse_data(article_rel_url):
        '''
        Parse data from article page tags

        Returns:
            Object
        '''

        article_url = urljoin(GazetteScraper.host, article_rel_url)
        soup = Scraper.get_url(article_url)

        print('Article: {url}'.format(url=article_url))

        title = soup.find('h1', 'title').text.strip()

       # Find publish date and convert to ISO time standard
        published = soup.find('div', 'story-pub-date').text.strip()
        published_iso = pendulum.parse(published, strict=False).isoformat()

        # Queen's gazette doesn't list authors, they either show an author
        # or show a team of authors under a team name. Anomalies include
        # showing two authors using 'with', such as 'By John with Alex'.
        # Gazette also includes author title such as "Alex, Communications".
        # Remove job title, and split by ' with ' to create authors array
        authors_raw = soup.find('div', 'story-byline').text.strip()[3:].split(',')[0]
        authors = authors_raw.split(' with ') if authors_raw else []

        content = soup.find('div', 'story-body').text.strip()
        content_raw = str(soup.find('div', 'story-body'))

        data = {
            'title': title,
            'slug': GazetteScraper.slug,
            'link': article_url,
            'published': published_iso,
            'updated': None,
            'authors': authors,
            'content': content,
            'contentRaw': content_raw,
            }

        return data
