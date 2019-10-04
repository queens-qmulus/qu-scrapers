"""
quartzscrapers.scrapers.news.news_helpers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains auxiliary functions for all of the news modules.
"""

import re
from urllib.parse import urljoin


def get_urls_on_depth(urls, logger, deep=False):
    """Get available URLS respective to its depth parameter.

    If deep is true, return all URLs since the site's inception. Otherwise,
    cap the urls related to the current only.

    Args:
        urls: List of urls.
        logger: Logging module.
        deep: Bool for a scrape of just the curent year, or every archive.

    Returns:
        List of all URLS or a subset of urls depending on 'deep' parameter.
    """
    if deep:
        logger.info('Deep scrape active. Scraping every article')
        return urls

    return [urls[0]]


def get_article_page(scraper, host_url, logger, article_rel_url):
    """Get BeautifulSoup object of an article page.

    Args:
        scraper: Base scraper object.
        host_url: Host URL in question.
        logger: Logging module.
        article_rel_url: Relative URL of article in question.

    Returns:
        Tuple of BeautifulSoup object of article page, and the article URL.
    """
    article_url = urljoin(host_url, article_rel_url)
    article_page = scraper.http_request(article_url)

    logger.debug('Article: {url}'.format(url=article_url))

    return article_page, article_url


def save_article(scraper, article_data, location):
    """Save textbook data to JSON.

    Args:
        scraper: Base scraper object.
        article_data: Dictionary of article data.
        location: location: String location of output file.
    """
    date, _ = article_data['published'].split('T')
    title_raw = article_data['url'].split('/')[-1]

    # Strip URL of ASCII-encoded characters, such as %20 or '+'.
    # Full reference list: https://www.w3schools.com/tags/ref_urlencode.asp.
    title = re.sub(r'(%[a-zA-Z0-9]{2}|[+])', '', title_raw)
    article_filename = '{date}_{title}'.format(date=date, title=title)

    scraper.write_data(article_data, article_filename, location)
