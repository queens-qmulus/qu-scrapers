import re
from pymongo import MongoClient
from urllib.parse import urljoin

from ..utils import Scraper
from .textbooks_helpers import get_google_books_info, normalize_string

class Textbooks:
    '''
    A scraper for Queen's textbooks.

    Queen's textbooks are located at the Queen's Campus boookstore.
    Current website: 'https://www.campusbookstore.com'
    '''

    host = 'https://www.campusbookstore.com'


    @staticmethod
    def scrape():
        '''Update database records for textbooks scraper'''

        # course department codes, such as CISC, ANAT, PHAR, etc..
        departments = Textbooks.get_departments('textbooks/search-engine')

        for department in departments:
            try:
                print('Course Department: {dep}'.format(dep=department))
                print('========================\n')

                course_rel_urls = Textbooks.get_course_rel_urls(
                    'textbooks/search-engine/results', department
                    )

                for course_rel_url in course_rel_urls:
                    textbook_data= []

                    try:
                        course_page, course_url = (
                            Textbooks.get_course_page(course_rel_url)
                            )

                        course_data = Textbooks.parse_course_data(course_page)

                        print('Course: {code} ({term})'.format(
                            code=course_data['code'], term=course_data['term'])
                            )
                        print('--------------------------')
                        print('Course Link: {url}\n'.format(url=course_url))

                        textbooks = course_page.find_all('div', 'textbookHolder')

                        print('{num} textbook(s) found\n'.format(num=len(textbooks)))

                        for textbook in textbooks:
                            try:
                                textbook_info = Textbooks.parse_textbook_data(
                                    textbook, course_url
                                    )

                                textbook_data.append(textbook_info)

                                Scraper.wait()

                            except Exception as ex:
                                Scraper.handle_error(ex, 'scrape')

                        if course_data or textbook_data:
                            Textbooks.preprocess_and_save_textbooks(
                                course_data, textbook_data
                                )

                        Scraper.wait()

                    except Exception as ex:
                        Scraper.handle_error(ex, 'scrape')

            except Exception as ex:
                Scraper.handle_error(ex, 'scrape')


    @staticmethod
    def get_departments(relative_url):
        '''
        Get list of department codes.

        Such department codes are: 'CISC', 'ANAT', 'PHAR', etc.

        Returns:
            List[String]
        '''

        campus_bookstore_url = urljoin(Textbooks.host, relative_url)
        soup = Scraper.http_request(campus_bookstore_url)

        departments_raw = soup.find_all('label', 'checkBoxContainer')
        departments = [dep.text.strip() for dep in departments_raw]

        return departments


    @staticmethod
    def get_course_rel_urls(relative_url, department):
        '''
        Get list of course relative URLs. This is done using the website's
        search bar. Department codes are inputted into the search bar and the
        resulting response has a list of courses related to the department.

        Note that some results will have courses unrelated to the department.
        For example, a department code of 'EG' will have course code results
        of 'ENGL', 'ENE', etc. For data integrity, this is filtered.

        Returns:
            List[String]
        '''

        course_rel_urls = []
        department_url = urljoin(Textbooks.host, relative_url)
        soup = Scraper.http_request(department_url, params=dict(q=department))

        # Use regex to filter textbooks having the right department substring
        regex = department + '[0-9]+'

        # filter to only retain one department code of courses
        courses_all = soup.find_all('h3')
        courses = [c for c in courses_all if re.search(regex, c.text)]

        print('{n} course(s) found\n'.format(n=len(courses)))

        for course in courses:
            try:
                course_details = course.next_sibling.next_sibling
                course_rel_url = course_details.find(
                    'dd', text=re.compile('Course=')
                    ).text.strip()

                course_rel_urls.append(course_rel_url)

            except Exception as ex:
                Scraper.handle_error(ex, 'get_course_rel_urls')

        return course_rel_urls


    @staticmethod
    def get_course_page(course_rel_url):
        '''
        Get HTML of course webpage given a course relative URL.

        Returns:
            Tuple[bs4.element.Tag, String]
        '''

        course_url = urljoin(Textbooks.host, course_rel_url)
        soup = Scraper.http_request(course_url)

        return soup, course_url


    @staticmethod
    def parse_course_data(course_page):
        '''
        Parse course data from course page

        Returns:
            Object
        '''

        regex = re.compile('[()]')

        # e.g: course text: EG553 (WINTER2018)
        course_code, course_term = (
            course_page.find('span', id='textbookCategory').text
                       .strip().split(' ')
            )

        instructors_raw = (
            [url for url in course_page.select('dd > a')
                if re.search('people', url['href'])][0]
            )

        instructors = (
            normalize_string(instructors_raw.text.strip().split(', '))
                if instructors_raw else []
            )

        # strip '(' and ')'
        term = regex.sub('', course_term)

        course_data = {
            'code': course_code,
            'term': term,
            'instructors': instructors
            }

        return course_data


    @staticmethod
    def parse_textbook_data(textbook, course_url):
        '''
        Parse textbook data from course page

        Returns:
            Object
        '''

        # === Info retrieved internally ===
        image_ref = urljoin(
            Textbooks.host,
            textbook.find('img', {'data-id': 'toLoad'})['data-url']
            )
        image_url = Scraper.http_request(image_ref, parse=False).text

        status_raw = textbook.find('dd', 'textbookStatus')
        status = status_raw.text.strip() if status_raw else None

        isbn_13 = (
            textbook.find('dt', text=re.compile('ISBN'))
                .next_sibling.next_sibling.text.strip()
            )

        print('Textbook ISBN: {isbn}'.format(isbn=isbn_13))

        # may need both new and old prices, or just new prices (or none)
        prices = textbook.find_all('dd', 'textbookPrice')
        price_new = price_used = None

        if prices:
            if len(prices) > 0 and '$' in prices[0].text:
                price_new = float(prices[0].text.strip()[1:])

            if len(prices) > 1 and '$' in prices[1].text:
                price_used = float(prices[1].text.strip()[1:])

        # == Info retrieved externally (via Google Books API) ==
        google_books_info = get_google_books_info(isbn_13)

        if google_books_info:
            title = google_books_info['title']
            authors = google_books_info['authors']
            isbn_10 = google_books_info['isbn_10'][0]
        else:
            title_raw, authors_raw = (
                textbook.select('div.textbookInfoHolder > h2')[0]
                    .text.strip().split('by')
                )

            title = title_raw.strip()
            authors = authors_raw.strip().replace('/', ', ').split(', ')
            isbn_10 = None

        # normalize names, whether from Google Books or Textbooks scraper
        authors = normalize_string(authors) if authors else []

        data = {
            'isbn_10': isbn_10,
            'isbn_13': isbn_13,
            'title': title,
            'authors': authors,
            'image': image_url,
            'price_new': price_new,
            'price_used': price_used,
            'link': course_url,
            'status': status
            }

        return data


    @staticmethod
    def preprocess_and_save_textbooks(course_data, textbook_data):
        '''
        Preprocess and save textbook data to database. There's course infor
        related to textbooks for this scraper. Because this is focused on
        textbooks, it parsess through each textbook, and appends the course
        data as the 'course' section, which is an array.

        If a textbook already exists in the database, course data is appended
        to the existing record. Otherwise, a brand new textbook record is
        created with the associated course information.
        '''

        client = MongoClient('localhost', 27017)
        db = client['knowledge']
        collection = 'textbooks'

        for textbook in textbook_data:
            isbn_13 = textbook['isbn_13']

            # textbook already exists, append course data to textbook data
            if db[collection].find_one({'isbn_13': isbn_13}):
                db[collection].find_one_and_update(
                    {'isbn_13': isbn_13},
                    {'$push': {'courses': course_data}}
                    )
            # textbook does not exist, add brand new document
            else:
                textbook['courses'] = [course_data]
                db[collection].insert(textbook)

        print('Data saved\n')
