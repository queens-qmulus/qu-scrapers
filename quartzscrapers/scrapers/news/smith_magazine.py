
import re
import time
import pendulum

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import add_default_fields, save_data, requests_retry_session

base_url = 'https://smith.queensu.ca'

def scrape_all():
    url = urljoin(base_url, 'magazine/archive')

    try:
        res = requests_retry_session().get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        archives = soup.find_all('div', 'field-content')
        links = [link.find('a')['href'] for link in archives]

        for link in links:
            print('ARCHIVE: {link}\n'.format(link=link))
            crawl_articles(link)

    except Exception as ex:
        print('Error in scrape_all(): {ex}'.format(ex=ex))


def crawl_articles(url):
    url = urljoin(base_url, url)

    try:
        res = requests_retry_session().get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        # Smith Magazine organizes their articles per magazine. Each magazine
        # has varying article sections, such as 'Features', 'Profiles', etc.
        # Each section lists a series of article links
        article_sections = soup.find('div', 'group-right').find_all('div', 'field')

    except Exception as ex:
        print('Error in crawl_articles(): {ex}'.format(ex=ex))

    for article_section in article_sections:
        results = []

        title = article_section.find('h2', 'block-title').text.strip()
        articles = article_section.find_all('span', 'field-content')

        print('Article Section: {section}'.format(section=title))
        print('--------------------------------')

        for article in articles:
            try:
                article_link = article.find('a')['href']
                article_data = scrape_article(article_link)

                if article_data:
                    results.append(article_data)

                print('Waiting 2 seconds...')
                time.sleep(2)

            except Exception as ex:
                print('Error in crawl_articles(): {ex}'.format(ex=ex))
                continue

        save_data(results, 'articles_smithmagazine')


def scrape_article(url):
    url = urljoin(base_url, url)
    data = {}

    print('Article: {url}'.format(url=url))

    try:
        res = requests_retry_session().get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        # Smith Magazine only shows issue season and year (Winter 217)
        # For the sake of news consistency, parse ISO only for the year.
        # It will always say  January 1st, with the respective year
        published = soup.find('div', 'field-name-field-issue').find('div', 'field-item').text.strip()
        published_iso = pendulum.parse(published[-4:]).isoformat()

        authors = soup.find('div', 'field-name-field-author')
        content_raw = soup.find('div', 'field-name-body')

        data = add_default_fields({
            'title': soup.find('div', 'field-name-title').text.strip(),
            'link': url,
            'published': published_iso,
            'updated': None,
            'authors': authors.find('div', 'field-item').text.strip().split(', ') if authors else [],
            'content': content_raw.text.strip() if content_raw else '',
            'contentRaw': str(content_raw) if content_raw else '',
            },
            'smithmagazine'
            )

        return data

    except Exception as ex:
        print('Error in scrape_article(): {ex}'.format(ex=ex))


if __name__ == '__main__':
    start_time = time.time()
    scrape_all()
    total_time = time.time() - start_time

    print('Total scrape took {seconds} s.\n'.format(seconds=total_time))
