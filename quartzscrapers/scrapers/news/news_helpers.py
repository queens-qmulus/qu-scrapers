import re

from ..utils import Scraper


def get_scrape_depth(urls, deep=False):
    if deep:
        print('Deep scrape active. Scraping every article\n')
        return urls
    else:
        return [urls[0]]

def save_article(article_data, location):
    date, _ = article_data['published'].split('T')
    title_raw = article_data['url'].split('/')[-1]

    # Strip URL of ASCII-encoded characters, such as %20 or '+'.
    # Full reference list: https://www.w3schools.com/tags/ref_urlencode.asp
    title = re.sub(r'(%[a-zA-Z0-9]{2}|[+])', '', title_raw)
    article_filename = '{date}_{title}'.format(date=date, title=title)

    Scraper.write_data(article_data, article_filename, location)
    print('Article data saved\n')