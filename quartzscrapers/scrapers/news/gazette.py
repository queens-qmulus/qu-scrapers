import re
import pendulum
from urllib.parse import urljoin

from ..utils import Scraper
from .news_helpers import save_article, get_article_page


class Gazette:
    '''
    Scraper for Queen's Gazette news source.
    '''

    host = 'http://www.queensu.ca'
    slug = 'gazette'
    scraper = Scraper()

    @staticmethod
    def scrape(
        deep=False,
        location='./dumps/news',
        relative_url='gazette/stories/all',
        slug=slug
    ):
        '''Parse information custom to Queen's Gazette'''

        num_pages = Gazette._get_num_pages(relative_url, deep)

        print('Total Pages: {num_pages}'.format(num_pages=num_pages))
        print('===================================\n')

        for page_index in range(num_pages):
            print('Page {page_num}'.format(page_num=(page_index + 1)))
            print('---------')

            try:
                article_rel_urls, article_issue_dates = (
                    Gazette._get_article_rel_urls(relative_url, page_index
                ))

                for article_rel_url, issue_date in zip(article_rel_urls, article_issue_dates):
                    try:
                        article_page, article_url = get_article_page(
                            Gazette.scraper, Gazette.host, article_rel_url)

                        article_data = Gazette._parse_article_data(
                            article_page, article_url, issue_date, slug)

                        if article_data:
                            save_article(
                                Gazette.scraper, article_data, location)

                        Gazette.scraper.wait()

                    except Exception as ex:
                        Gazette.scraper.handle_error(ex, 'scrape')

            except Exception as ex:
                Gazette.scraper.handle_error(ex, 'scrape')

    @staticmethod
    def _get_num_pages(relative_url, deep):
        '''
        Request URL for all archived articles and parse number of pages to
        crawl.

        Returns:
            Int
        '''

        params = {}

        if deep:
            print('Deep scrape active. Scraping every article\n')
        else:
            year = pendulum.now().format('YYYY')
            params.update({
                'field_publication_date_value[min][date]': '{}-01-01'.format(year),
                'field_publication_date_value[max][date]': '{}-12-31'.format(year),
            })

        stories_all_url = urljoin(Gazette.host, relative_url)
        soup = Gazette.scraper.http_request(stories_all_url, params=params)

        page_url = soup.find('li', 'pager-last').find('a')['href']

        # get last two digits from link of last page, i.e;
        # '/story/archive/news/2012/?page=13' results in 13
        index = page_url.rfind('=')
        num_pages = int(page_url[(index + 1):]) + 1 # +1 to go from 0 to n

        return num_pages

    @staticmethod
    def _get_article_rel_urls(relative_url, page_index):
        '''
        Gets list of relative URLs for articles. Queen's Gazette displays
        approximately 16 articles per page.

        Returns:
            List[String]
        '''

        article_url = urljoin(Gazette.host, relative_url)
        soup =  Gazette.scraper.http_request(article_url, params=dict(page=page_index))

        articles = soup.find_all('div', class_='story-info')

        article_issues = soup.find_all('div', class_='story-issue')
        article_rel_urls = [article.find('a')['href'] for article in articles]

        # For alumnireview, there's no published dates due this outlet being
        # an issue-based resource. Parse issue-date year at least for a
        # date of YYYY-XX-XX
        article_issue_dates = [
            article.find('div', class_='story-issue') for article in articles
        ]

        return article_rel_urls, article_issue_dates


    @staticmethod
    def _get_article_page(article_rel_url):
        article_url = urljoin(Gazette.host, article_rel_url)
        article_page = Gazette.scraper.http_request(article_url)

        print('Article: {url}'.format(url=article_url))

        return article_page, article_url


    @staticmethod
    def _parse_article_data(article_page, article_url, issue_date, slug):
        '''
        Parse data from article page tags

        Returns:
            Object
        '''

        title = article_page.find('h1', 'title').text.strip()

        # Find publish date and convert to ISO time standard
        published_raw = article_page.find('div', 'story-pub-date')

        if published_raw:
            published = published_raw.text.strip()
            published_iso = pendulum.parse(published, strict=False).isoformat()
        else:
            # no date for AlumniReview. Use issue year
            issue_year = re.search(r'\d{4}', issue_date.text).group(0)
            published_iso = pendulum.parse(issue_year).isoformat()

        # Queen's gazette doesn't list authors, they either show an author
        # or show a team of authors under a team name. Anomalies include
        # showing two authors using 'with', such as 'By John with Alex'.
        # Gazette also includes author title such as "Alex, Communications".
        # Remove job title, and split by ' with ' to create authors array
        authors_raw = (
            article_page.find('div', 'story-byline').text.strip()[3:].split(',')[0]
            )
        authors = authors_raw.split(' with ') if authors_raw else []

        content = article_page.find('div', 'story-body').text.strip()
        content_raw = str(article_page.find('div', 'story-body'))

        data = {
            'title': title,
            'slug': slug,
            'url': article_url,
            'published': published_iso,
            'updated': published_iso,
            'authors': authors,
            'content': content,
            'content_raw': content_raw,
            }

        return data
