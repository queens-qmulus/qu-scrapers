import re
from pymongo import MongoClient
from urllib.parse import urljoin

from ..utils import Scraper
from .textbooks_helpers import (
    get_google_books_info,
    normalize_string,
    save_textbook_data
    )


class Textbooks:
    '''
    A scraper for Queen's textbooks.

    Queen's textbooks are located at the Queen's Campus boookstore.
    Current website: 'https://www.campusbookstore.com'
    '''

    host = 'https://www.campusbookstore.com'

    @staticmethod
    def scrape(location='./dumps/textbooks'):
        '''Update database records for textbooks scraper'''

        # course department codes, such as CISC, ANAT, PHAR, etc..
        departments = Textbooks._get_departments('textbooks/search-engine')

        for department in departments:
            try:
                print('Course Department: {dep}'.format(dep=department))
                print('========================\n')

                course_rel_urls = Textbooks._get_course_rel_urls(
                    'textbooks/search-engine/results', department
                )

                for course_rel_url in course_rel_urls:
                    textbook_data = []

                    try:
                        course_page, course_url = (
                            Textbooks._get_course_page(course_rel_url)
                        )

                        course_data = Textbooks._parse_course_data(
                            course_page
                        )

                        if course_data:
                            cd = course_data[0]
                            term = ''

                            if len(course_data) == 1:
                                term = cd['term']
                            else:
                                term = 'Fall and Winter'

                            print('Course: {dep}{code} ({term} {year})'.format(
                                dep=cd['department'],
                                code=cd['course_code'],
                                term=term,
                                year=cd['year']
                            ))
                        else:
                            print('** No course data available')

                        print('--------------------------')
                        print('Course Link: {}\n'.format(course_url))

                        textbooks = course_page.find_all(
                            'div', 'textbookHolder'
                        )

                        print('{} textbook(s) found\n'.format(len(textbooks)))

                        for textbook in textbooks:
                            try:
                                textbook_info = (
                                    Textbooks._parse_textbook_data(
                                        textbook, course_url
                                    )
                                )

                                textbook_data.append(textbook_info)

                                Scraper.wait()

                            except Exception as ex:
                                Scraper.handle_error(ex, 'scrape')

                        if course_data or textbook_data:
                            save_textbook_data(
                                course_data, textbook_data, location)

                        Scraper.wait()

                    except Exception as ex:
                        Scraper.handle_error(ex, 'scrape')

            except Exception as ex:
                Scraper.handle_error(ex, 'scrape')

    @staticmethod
    def _get_departments(relative_url):
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
    def _get_course_rel_urls(relative_url, department):
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
                Scraper.handle_error(ex, '_get_course_rel_urls')

        return course_rel_urls

    @staticmethod
    def _get_course_page(course_rel_url):
        '''
        Get HTML of course webpage given a course relative URL.

        Returns:
            Tuple[bs4.element.Tag, String]
        '''

        course_url = urljoin(Textbooks.host, course_rel_url)
        soup = Scraper.http_request(course_url)

        return soup, course_url

    @staticmethod
    def _parse_course_data(course_page):
        '''
        Parse course data from course page

        Returns:
            Object
        '''

        def split_string(string):
            return re.sub(r'([a-zA-Z]+)([0-9]+)', r'\1,\2', string).split(',')

        course_list = []
        regex = re.compile('[()]')

        # e.g: course text: ENGL223 (WINTER2018)
        dep_course_code, year_term = (
            course_page.find('span', id='textbookCategory').text
                       .strip().split(' ')
        )

        # turns ENGL223 to ENGL and 223
        department, course_code = split_string(dep_course_code)

        # strips '(' and ')' and turns (WINTER2018) WINTER and 2018
        term_str, year = split_string(regex.sub('', year_term))

        # filter for 'FW' and label as individual terms
        terms = re.sub('FW', 'Fall,Winter', term_str).split(',')

        if len(year) == 2:
            year = ''.join(('20', year))

        instructors_raw = (
            [url for url in course_page.select('dd > a')
                if re.search('people', url['href'])][0]
        )

        instructors = (
            normalize_string(instructors_raw.text.strip().split(', '))
            if instructors_raw else []
        )

        course_data = {
            'year': year,
            'term': '',
            'department': department,
            'course_code': course_code,
            'instructors': instructors
        }

        for term in terms:
            course_data['term'] = term.lower().capitalize()
            course_list.append(course_data)

        return course_list

    @staticmethod
    def _parse_textbook_data(textbook, course_url):
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

