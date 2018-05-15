import pendulum
from urllib.parse import urljoin

from ..utils import Scraper

class AlumniReviewScraper:
    '''
    Scraper for Queen's Alumni Review news source.
    '''

    host = 'http://www.queensu.ca'
    slug = 'alumnireview'

    @staticmethod
    def scrape(collection='articles'):
        '''
        Parse information custom to Queen's Alumni Review. This is a
        subcategory under Queen's Gazette.
        '''

        num_pages = AlumniReviewScraper.get_num_pages(
            'gazette/alumnireview/stories'
            )

        print('Total Pages: {num_pages}'.format(num_pages=num_pages))
        print('===================================\n')

        for page_index in range(num_pages):
            print('Page {page_num}'.format(page_num=(page_index + 1)))
            print('---------')
            results = []

            try:
                article_rel_urls = AlumniReviewScraper.get_article_rel_urls(
                    'gazette/alumnireview/stories', page_index
                    )

                for article_rel_url in article_rel_urls:
                    try:
                        article_data = AlumniReviewScraper.parse_data(
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

    @staticmethod
    def get_num_pages(relative_url):
        '''
        Request URL for all archived articles and parse number of pages to
        crawl.

        Returns:
            Int
        '''

        stories_all_url = urljoin(AlumniReviewScraper.host, relative_url)
        soup = Scraper.get_url(stories_all_url)

        page_link = soup.find('li', 'pager-last').find('a')['href']
        index = page_link.rfind('=')
        num_pages = int(page_link[(index + 1):]) + 1

        return num_pages

    @staticmethod
    def get_article_rel_urls(relative_url, page_index):
        '''
        Gets list of relative URLs for articles. Queen's Alumni Review
        displays approximately 16 articles per page.

        Returns:
            List[String]
        '''

        article_url = urljoin(AlumniReviewScraper.host, relative_url)
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
        published_iso = None

        article_url = urljoin(AlumniReviewScraper.host, article_rel_url)
        soup = Scraper.get_url(article_url)

        print('Article: {url}'.format(url=article_url))

        title = soup.find('h1', 'title').text.strip()

       # Find publish date and convert to ISO time standard
        published_raw = soup.find('div', 'story-pub-date')

        if published_raw:
            published = published_raw.text.strip()
            published_iso = pendulum.parse(published, strict=False).isoformat()

        # Queen's gazette doesn't list authors, they either show an author
        # or show a team of authors under a team name. Anomalies include
        # showing two authors using 'with', such as 'By John with Alex'.
        # Gazette also includes author title such as "Alex, Communications".
        # Remove job title, and split by ' with ' to create authors array
        authors_raw = (
            soup.find('div', 'story-byline').text.strip()[3:].split(',')[0]
            )
        authors = authors_raw.split(' with ') if authors_raw else []

        content = soup.find('div', 'story-body').text.strip()
        content_raw = str(soup.find('div', 'story-body'))

        data = {
            'title': title,
            'slug': AlumniReviewScraper.slug,
            'link': article_url,
            'published': published_iso,
            'updated': published_iso,
            'authors': authors,
            'content': content,
            'contentRaw': content_raw,
            }

        return data
