import re
from urllib.parse import urljoin


def get_urls_on_depth(urls, logger, deep=False):
    if deep:
        logger.info('Deep scrape active. Scraping every article')
        return urls
    else:
        return [urls[0]]

def get_article_page(scraper, host_url, logger, article_rel_url):
    article_url = urljoin(host_url, article_rel_url)
    article_page = scraper.http_request(article_url)

    logger.debug('Article: {url}'.format(url=article_url))

    return article_page, article_url

def save_article(scraper, article_data, location):
    date, _ = article_data['published'].split('T')
    title_raw = article_data['url'].split('/')[-1]

    # Strip URL of ASCII-encoded characters, such as %20 or '+'.
    # Full reference list: https://www.w3schools.com/tags/ref_urlencode.asp
    title = re.sub(r'(%[a-zA-Z0-9]{2}|[+])', '', title_raw)
    article_filename = '{date}_{title}'.format(date=date, title=title)

    scraper.write_data(article_data, article_filename, location)
