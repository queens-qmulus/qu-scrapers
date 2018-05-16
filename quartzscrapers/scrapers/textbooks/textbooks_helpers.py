from ..utils import Scraper

def get_google_books_info(isbn_13):
    '''
    Retrieve additional textbook information missing from Queen's Campus
    Bookstore via Google Books API.

    Returns:
        Object
    '''

    data = {}

    response = Scraper.get_url(
        url='https://www.googleapis.com/books/v1/volumes',
        params=dict(q='ibsn:{isbn}'.format(isbn=isbn_13)),
        ).json()

    if response.get('items'):
        response = response['items'][0]['volumeInfo']

        isbns = response['industryIdentifiers']
        title = response['title'].strip()
        authors = response['authors']

        # API shows both isbn 10 and 13 in an array of any order.
        # Sometimes it shows unrelated data, such as
        # [{'type': 'OTHER', 'identifier': 'UOM:39015061016815'}]
        isbn_10 = (
            [isbn['identifier'] for isbn in isbns if isbn['type'] == 'ISBN_10']
            )

        if response.get('subtitle'):
            subtitle = response['subtitle']
            title = '{title}: {sub}'.format(title=title, sub=subtitle)

        data = {
            'isbn_10': isbn_10,
            'title': title,
            'authors': authors,
            }

    return data


def normalize_string(names):
    '''
    Format string to be lowercase and capitalized, per word in string.
    E.g.: 'FOO BAR' becomes 'Foo Bar'

    Returns:
        String
    '''

    new_names = []

    for name in names:
        new_names.append(
            ' '.join([n.lower().capitalize() for n in name.split(' ')])
            )

    return new_names

