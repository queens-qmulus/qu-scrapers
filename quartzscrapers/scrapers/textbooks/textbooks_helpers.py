from ..utils.config import GOOGLE_BOOKS_KEY


def get_google_books_info(isbn_13, scraper):
    '''
    Retrieve additional textbook information missing from Queen's Campus
    Bookstore via Google Books API.

    Returns:
        Object
    '''

    data = {}

    response = scraper.http_request(
        parse=False,
        url='https://www.googleapis.com/books/v1/volumes',
        params=dict(q='ibsn:{isbn}',key='{key}'.format(
            isbn=isbn_13,
            key=GOOGLE_BOOKS_KEY)
        )
    ).json()

    if response.get('items'):
        response = response['items'][0]['volumeInfo']

        isbns = response.get('industryIdentifiers', '')
        title = response.get('title', '').strip()
        authors = response.get('authors', '')

        # API shows both isbn 10 and 13 in an array of any order.
        # Sometimes it shows unrelated data, such as
        # [{'type': 'OTHER', 'identifier': 'UOM:39015061016815'}]
        isbn_10 = (
            [isbn.get('identifier') for isbn in isbns if isbn['type'] == 'ISBN_10']
        )

        if response.get('subtitle'):
            subtitle = response.get('subtitle')
            title = '{title}: {sub}'.format(title=title, sub=subtitle)

        data = {
            'isbn_10': isbn_10 or [''],
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

def save_textbook_data(course_list, textbook_list, scraper, location):
    '''Preprocess and save textbook data to JSON.

    Course information is related to textbooks. Because this is focused on
    textbooks, it parsess through each textbook, and appends the course
    data as the 'course' section, which is an array.

    If a textbook already exists in the database, course data is appended
    to the existing record. Otherwise, a brand new textbook record is
    created with the associated course information.
    '''

    for course_data in course_list:
        for textbook_data in textbook_list:
            filename = '{year}_{isbn}'.format(
                year=course_data['year'],
                isbn=textbook_data['isbn_13'],
            )

            scraper.update_data(
                textbook_data, course_data, 'courses', filename, location)
