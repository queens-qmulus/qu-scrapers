#  http://www.queensu.ca/gazette/alumnireview/stories

import re
import time
import pendulum

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import add_default_fields, save_data, requests_retry_session

base_url = 'http://www.queensu.ca'

def scrape_all():
    url = urljoin(base_url, 'gazette/alumnireview/stories')

    try:
        res = requests_retry_session().get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        page_link = soup.find('li', 'pager-last').find('a')['href']
        index = page_link.rfind('=')
        num_pages = int(page_link[(index + 1):]) + 1 # +1 to go from 0 to n

        crawl_pages(url, num_pages)

    except Exception as ex:
        print('Error in scrape_all(): {ex}'.format(ex=ex))


def crawl_pages(url, num_pages):
    print('Total Pages: {num_pages}'.format(num_pages=num_pages))
    print('===================================\n')

    for i in range(num_pages):
        results = []

        print('Page {page_num}'.format(page_num=i))
        print('---------')

        try:
            res = requests_retry_session().get(url, params=dict(page=i), timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')

            articles = soup.find_all('div', 'story-title')

            for article in articles:
                article_link = article.find('a')['href']
                article_data = scrape_article(article_link)

                if article_data:
                    results.append(article_data)

                print('Waiting 2 seconds...')
                time.sleep(2)

            save_data(results, 'articles_alumnireview')

        except Exception as ex:
            print('Error in crawl_pages(): {ex}'.format(ex=ex))
            continue


def scrape_article(url):
    url = urljoin(base_url, url)
    data = {}

    print('Article: {url}'.format(url=url))

    try:
        res = requests_retry_session().get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        # Queen's gazette doesn't list authors, they either show an author
        # or show a team of authors under a team name. Anomalies include
        # showing two authors using 'with', such as 'By John with Alex'.
        # Gazette also includes author title such as "Alex, Communications".
        # Remove job title, and split by ' with ' to create authors array
        authors = soup.find('div', 'story-byline')

        content_raw = soup.find('div', 'story-body')

        # No listed published/updated date for Gazette's Alumni Review
        data = add_default_fields({
            'title': soup.find('h1', 'title').text.strip(),
            'link': url,
            'published': '',
            'updated': '',
            'authors': authors.text.strip()[3:].split(' with ') if authors else [],
            'content': content_raw.text.strip(),
            'contentRaw': str(content_raw),
            },
            'alumnireview'
            )

        return data

    except Exception as ex:
        print('Error in scrape_article(): {ex}'.format(ex=ex))
        return


if __name__ == '__main__':
    start_time = time.time()
    scrape_all()
    total_time = time.time() - start_time

    print('Total scrape took {seconds} s.\n'.format(seconds=total_time))
