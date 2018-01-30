import re
import time
import requests
import pendulum

from bs4 import BeautifulSoup
from pymongo import MongoClient
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

base_url = 'http://www.queensjournal.ca'
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp, */*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch, br',
    'Accept-Language': 'en-US,en;q=0.8',
    'Cache-Control': 'no-cache',
    'dnt': '1',
    'Pragma': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
}

def scrape_all():
    url = urljoin(base_url, '/news')

    try:
        res = requests_retry_session().get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        archive_links = soup.find('ul', 'views-summary').find_all('li')
        links = [link.find('a')['href'] for link in archive_links]

        for link in links:
            print('ARCHIVE: {link}'.format(link=link))
            crawl_year(link)

    except Exception as ex:
        print('Error in scrape_all(): {ex}'.format(ex=ex))


def crawl_year(url):
    url = urljoin(base_url, url)

    try:
        res = requests_retry_session().get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        page_title = soup.find('div', id='content').find('h1').text.strip()
        last_page = soup.find('li', 'pager-last')
        page_link = last_page.find('a')['href'] if last_page else 'page=0'

        # get last two digits from link of last page, i.e;
        # '/story/archive/news/2017/?page=13' results in 13
        index = page_link.rfind('=')
        num_pages = int(page_link[(index + 1):]) + 1 # +1 to go from 0 to n

        crawl_pages(url, num_pages)

    except Exception as ex:
        print('Error in crawl_year(): {ex}'.format(ex=ex))
        return


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

            articles = soup.find_all('div', 'node-story')

            for article in articles:
                article_link = article.find('h2').find('a')['href']
                article_data = scrape_article(article_link)

                if article_data:
                    results.append(article_data)

                print('Waiting 2 seconds...')
                time.sleep(2)

            save_article(results)

        except Exception as ex:
            print('Error in crawl_pages(): {ex}'.format(ex=ex))
            continue


def scrape_article(url):
    url = urljoin(base_url, url)
    regex_str = 'Last Updated: '
    updated_iso = None
    data = {}

    print('Article: {url}'.format(url=url))

    try:
        res = requests_retry_session().get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        # Find publish date and convert to ISO time standard
        published = soup.find('li', 'date').text.strip()
        published_iso = pendulum.parse(published).isoformat()

        # Find updated date if it exists, and convert to ISO time standard.
        # NOTE: queensjournal.ca unofficially adds a bolded sentence within article
        # stating 'Last Updated:' with the date. Use regex to find this tag, and if
        # it exists, scrape the date and convert to ISO time standard
        updated_raw = soup.find(text=re.compile(regex_str))

        if updated_raw:
            updated = updated_raw.strip()[len(regex_str):]
            updated_iso = pendulum.parse(updated).isoformat()

        authors = soup.find('li', 'authors')

        data = add_default_fields({
            'title': soup.find('div', id='content').find('h1').text.strip(),
            'link': url[:-1],
            'published': published_iso,
            'updated': updated_iso,
            'authors': authors.text.strip().split(', ') if authors else [],
            'content': soup.find('div', 'field-name-body').text.strip(),
            'contentRaw': str(soup.find('div', 'field-name-body')),
            })

        return data
    except Exception as ex:
        print('Error in scrape_article(): {ex}'.format(ex=ex))
        return


def add_default_fields(data):
    if not data.get('updated'):
        data['updated'] = data['published']

    data['slug'] = 'queensjournal'

    return data


def save_article(data):
    client = MongoClient('localhost', 27017)
    db = client['knowledge']

    db.articles.insert_many(data)
    print('\nArticles saved\n')


# Adapter for requests library to handle automatic retries with exponential
# backoff. Inspired by Peter Bengtsson
# Source: https://www.peterbe.com/plog/best-practice-with-retries-with-requests
def requests_retry_session(
    retries=5,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None
):
    session = session or requests.Session()
    session.headers.update(headers)

    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session


if __name__ == '__main__':
    start_time = time.time()
    scrape_all()
    total_time = time.time() - start_time

    print('Total scrape took {seconds} s.\n'.format(seconds=total_time))
