#  http://www.queensu.ca/gazette/alumnireview/stories

import re
import time
import pendulum

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import add_default_fields, save_data, requests_retry_session

base_url = 'http://www.juris-diction.ca'

def scrape_all():
    try:
        res = requests_retry_session().get(base_url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        archive_links = soup.find('div', id='archives-3').find_all('li')
        links = [link.find('a')['href'] for link in archive_links]

        for link in links:
            res = requests_retry_session().get(link, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')

            print('ARCHIVE: {link}'.format(link=link))
            crawl_pages(link, soup)

    except Exception as ex:
        print('Error in scrape_all(): {ex}'.format(ex=ex))


def crawl_pages(url, soup):
    page_num = 1

    # paginate until we no longer see a 'next' button
    while soup.find('a', 'next'):
        print('Page {page_num}\n'.format(page_num=page_num))
        print('---------')

        crawl_articles(soup)

        page_num += 1
        url = soup.find('a', 'next')['href']

        try:
            res = requests_retry_session().get(url, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
        except Exception as ex:
            print('Error in crawl_pages(): {ex}'.format(ex=ex))
            continue

    # crawl last page with no 'next' button
    print('\nPage {page_num}'.format(page_num=page_num))
    print('---------')
    crawl_articles(soup)


def crawl_articles(soup):
    results = []

    try:
        article_section = soup.find('div', 'vw-isotope')
        articles = article_section.find_all('h3', 'vw-post-box-title')

        for article in articles:
            article_link = article.find('a')['href']
            article_data = scrape_article(article_link)

            if article_data:
                results.append(article_data)

            print('Waiting 2 seconds...')
            time.sleep(2)

        save_data(results, 'articles_jurisdiction')

    except Exception as ex:
        print('Error in crawl_pages(): {ex}'.format(ex=ex))


def scrape_article(url):
    url = urljoin(base_url, url)
    data = {}

    print('Article: {url}'.format(url=url))

    try:
        res = requests_retry_session().get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        # Queen's Juris Diction uses HTML5 element 'time', which already 
        # contains ISO format in 'datetime' attribute
        published_iso = soup.find('time')['datetime']

        # Multiple authors are listed with commas, except for last author with
        # 'and' such as 'John, Alex and Jason'.
        authors = soup.find('a', 'author-name')

        content_raw = soup.find('div', 'vw-post-content')

        data = add_default_fields({
            'title': soup.find('h1', 'entry-title').text.strip(),
            'link': url[:-1],
            'published': published_iso,
            'updated': None,
            'authors': authors.text.replace(' and', ',').split(', ') if authors else [],
            'content': content_raw.text.strip(),
            'contentRaw': str(content_raw),
            },
            'jurisdiction'
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
