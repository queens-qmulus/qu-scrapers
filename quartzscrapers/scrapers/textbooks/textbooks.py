import re
import time

from bs4 import BeautifulSoup
from pymongo import MongoClient
from urllib.parse import urljoin
from utils import requests_retry_session

base_url = 'https://www.campusbookstore.com'

def scrape():
    url = urljoin(base_url, 'textbooks/search-engine')

    try:
        res = requests_retry_session().get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        # course department codes, such as CISC, ANAT, PHAR, etc..
        departments = soup.find_all('label', 'checkBoxContainer')

        for department in departments:
            department = department.text.strip()

            print('Course Department: {dep}'.format(dep=department))
            print('========================\n')

            crawl_department(department)

    except Exception as ex:
        print('Error in scrape(): {ex}'.format(ex=ex))


def crawl_department(department):
    url = urljoin(base_url, 'textbooks/search-engine/results')

    try:
        res = requests_retry_session().get(url, timeout=10, params=dict(q=department))
        soup = BeautifulSoup(res.text, 'html.parser')

        # Because we find results via the search bar with department codes,
        # we could get unrelated information on the following page. Example:
        # searching for department code EG will show results for ENGL, ENE, etc
        # use regex to filter for textbooks having the right department substring
        regex = department + '[0-9]+'

        # filter to only retain one department code of courses
        courses_all = soup.find_all('h3')
        courses = [c for c in courses_all if re.search(regex, c.text)]

        print('{num} course(s) found\n'.format(num=len(courses)))

        # Due to campusbookstore.com's HTML markup, we have to pair the course
        # titles and the course links together, assuming they're always going
        # to be the same length. Use the zip() function for this
        for course in courses:
            try:
                print('Course: {course}'.format(course=course.text.strip()))
                print('-------------------')

                # includes <dl> tag of course instructor, course link, etc
                course_details = course.next_sibling.next_sibling

                course_link = course_details.find(
                    'dd', text=re.compile('Course=')
                    ).text.strip()

                #Return type: (Object, Array)
                course_data, textbook_data = scrape_textbooks(course_link)

                if course_data or textbook_data:
                    preprocess_textbooks(course_data, textbook_data)

                print('Waiting 2 seconds before next course...')
                time.sleep(2)

            except Exception as ex:
                print('Error in crawl_department(): {ex}'.format(ex=ex))
                continue

    except Exception as ex:
        print('Error in crawl_department(): {ex}'.format(ex=ex))


def scrape_textbooks(url):
    url = urljoin(base_url, url)
    regex = re.compile('[()]')
    textbook_data = []

    print('Course Link: {url}'.format(url=url))

    try:
        res = requests_retry_session().get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        # Course bundle

        # e.g: course text: EG553 (WINTER2018)
        course_code, course_term = soup.find('span', id='textbookCategory').text.strip().split(' ')
        instructors_raw = [link for link in soup.select('dd > a') if re.search('people', link['href'])][0]
        instructors = (normalize_names(instructors_raw.text.strip().split(', '))
                if instructors_raw else []
            )

        course_data = {
            'code': course_code,
            'term': regex.sub('', course_term), # strip '(' and ')'
            'instructors': instructors
        }

        textbooks = soup.find_all('div', 'textbookHolder')

        print('{num} textbook(s) found\n'.format(num=len(textbooks)))

        # Textbook bundle
        for textbook in textbooks:
            # === Info retrieved internally ===
            image_ref = urljoin(
                base_url,
                textbook.find('img', {'data-id': 'toLoad'})['data-url']
                )
            image_link = requests_retry_session().get(image_ref).text

            status = textbook.find('dd', 'textbookStatus')
            isbn_13 = textbook.find('dt', text=re.compile('ISBN')).next_sibling.next_sibling.text.strip()

            print('Textbook ISBN: {isbn}'.format(isbn=isbn_13))

            # may new both new and old prices, or just new prices (or none)
            prices = textbook.find_all('dd', 'textbookPrice')
            price_new = None
            price_used = None

            if prices:
                if len(prices) > 0 and '$' in prices[0].text:
                    price_new = float(prices[0].text.strip()[1:])

                if len(prices) > 1 and '$' in prices[1].text:
                    price_used = float(prices[1].text.strip()[1:])

            # == Info retrieved externally (via Google Books API) ==
            isbn_10 = None

            google_books_res = requests_retry_session().get(
                'https://www.googleapis.com/books/v1/volumes',
                params=dict(q='ibsn:{isbn}'.format(isbn=isbn_13))
                ).json()

            if google_books_res.get('items'):
                response = google_books_res['items'][0]['volumeInfo']

                isbns = response['industryIdentifiers']

                # API shows both isbn 10 and 13 in an array of any order.
                # Somethings it shows unrelated data, such as
                # [{'type': 'OTHER', 'identifier': 'UOM:39015061016815'}]
                isbn_10 = [isbn['identifier'] for isbn in isbns if isbn['type'] == 'ISBN_10']
                title = response['title']
                authors = response['authors']

                if response.get('subtitle'):
                    subtitle = response['subtitle']
                    title = '{title}: {sub}'.format(title=title, sub=subtitle)
            else:
                title, authors_raw = textbook.select('div.textbookInfoHolder > h2')[0].text.strip().split('by')
                authors = authors_raw.strip().replace('/', ', ').split(', ')

            data = {
                'isbn_10': isbn_10[0] if isbn_10 else '',
                'isbn_13': isbn_13,
                'title': title.strip(),
                'authors': normalize_names(authors) if authors else [],
                'image': image_link,
                'price_new': price_new,
                'price_used': price_used,
                'link': url,
                'status': status.text.strip() if status else ''
            }

            textbook_data.append(data)

            print('Waiting 2 seconds before next textbook...')
            time.sleep(2)

        return course_data, textbook_data

    except Exception as ex:
        print('Error in scrape_textbooks(): {ex}'.format(ex=ex))


# turns 'FOO BAR' into 'Foo Bar'
def normalize_names(names):
    new_names = []

    for name in names:
        new_names.append(
            ' '.join([n.lower().capitalize() for n in name.split(' ')])
            )

    return new_names


# Courses-to-textbooks will be a n-to-n relationship.
# Save data based on textbook only, meaning parse through each
# textbook, and append the course data to the textbook as the
# 'course' section. 'course' is an array, so we'll be appending
# courses to the 'course' array, unless that course is already
# there. Check if a document in the 'textbooks' collection
# already exists for a certain textbook. That way we only
# append course info rather than overwrite the whole document
# with the same textbook info. Q.E.D
def preprocess_textbooks(course_data, textbooks):
    client = MongoClient('localhost', 27017)
    db = client['knowledge']
    collection = 'textbooks'

    for textbook in textbooks:
        isbn_13 = textbook['isbn_13']

        # we've seen this textbook before, append course data to textbook data
        if db[collection].find_one({'isbn_13': isbn_13}):
            db[collection].find_one_and_update(
                {'isbn_13': isbn_13},
                {'$push': {'courses': course_data}}
                )
        # we have not seen this textbook before, add brand new document
        else:
            textbook['courses'] = [course_data]
            db[collection].insert(textbook)

    print('\nData saved\n')

if __name__ == '__main__':
    start_time = time.time()
    scrape()
    total_time = time.time() - start_time

    print('Total scrape took {seconds} s.\n'.format(seconds=total_time))
