import requests

from pymongo import MongoClient
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

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

def add_default_fields(data, slug):
    if not data.get('updated'):
        data['updated'] = data['published']

    data['slug'] = slug

    return data


def save_data(data, collection):
    client = MongoClient('localhost', 27017)
    db = client['knowledge']

    db[collection].insert_many(data)
    print('\nData saved\n')


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