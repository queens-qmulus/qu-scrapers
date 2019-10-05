"""
quartzscrapers.scrapers.textbooks.textbooks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the Textbooks class scraper for parsing textbook data.
"""

import re
from urllib.parse import urljoin
from collections import OrderedDict

from bs4.element import Tag

from ..utils import Scraper
from .textbooks_helpers import (
    get_google_books_info,
    normalize_string,
    save_textbook_data
    )


class Textbooks:
    """A scraper for Queen's textbooks.

    Queen's textbooks are located at the Queen's Campus boookstore.
    Current website: <https://www.campusbookstore.com>.
    """

    scraper_key = 'textbooks'
    location = './dumps/{}'.format(scraper_key)
    host = 'https://www.campusbookstore.com'
    scraper = Scraper()
    logger = scraper.logger

    @staticmethod
    def scrape(location=location, *args, **kwargs):
        """Scrape textbook information to JSON files.

        Args:
            location (optional): String location output files.
        """
        Textbooks.logger.info('Starting Textbooks scrape')

        # Course department codes, such as CISC, ANAT, PHAR, etc..
        departments = Textbooks._get_departments('textbooks/search-engine')

        for department in departments:
            try:
                Textbooks.logger.debug('Course Department: %s', department)

                course_rel_urls = Textbooks._get_course_rel_urls(
                    'textbooks/search-engine/results', department
                )

                for course_rel_url in course_rel_urls:
                    textbook_data = []

                    try:
                        course_page, course_url = Textbooks._get_course_page(
                            course_rel_url)

                        course_data = Textbooks._parse_course_data(
                            course_page, course_url)

                        if not course_data:
                            Textbooks.logger.debug('No course data available')
                        else:
                            data = course_data[0]
                            term = ''

                            if len(course_data) == 1:
                                term = data['term']
                            else:
                                term = 'Multiple terms'

                            str_course = '{dep}{code} ({term} {year})'.format(
                                dep=data['department'],
                                code=data['course_code'],
                                term=term,
                                year=data['year']
                            )

                            Textbooks.logger.debug(str_course)

                        Textbooks.logger.debug('Course Link: %s', course_url)

                        textbooks = course_page.find_all(
                            'div', 'textbookHolder'
                        )

                        Textbooks.logger.debug(
                            '%s textbook(s) found', len(textbooks))

                        for textbook in textbooks:
                            try:
                                textbook_info = (
                                    Textbooks._parse_textbook_data(textbook)
                                )

                                textbook_data.append(textbook_info)

                                Textbooks.scraper.wait()

                            except Exception:
                                Textbooks.scraper.handle_error()

                        if course_data or textbook_data:
                            save_textbook_data(
                                course_data,
                                textbook_data,
                                Textbooks.scraper,
                                location
                            )

                        Textbooks.logger.debug('Textbook data saved')
                        Textbooks.scraper.wait()

                    except Exception:
                        Textbooks.scraper.handle_error()

            except Exception:
                Textbooks.scraper.handle_error()

        Textbooks.logger.info('Completed Textbooks scrape')

    @staticmethod
    def _get_departments(relative_url):
        # Get list of department codes.
        # Such department codes are: 'CISC', 'ANAT', 'PHAR', etc.

        campus_bookstore_url = urljoin(Textbooks.host, relative_url)
        soup = Textbooks.scraper.http_request(campus_bookstore_url)

        departments_raw = soup.find_all('label', 'checkBoxContainer')
        departments = [dep.text.strip() for dep in departments_raw]

        return departments

    @staticmethod
    def _get_course_rel_urls(relative_url, department):
        # Get list of course relative URLs.

        # This is done using the website's search bar. Department codes are
        # inputted into the search bar and the resulting response has a list of
        # courses related to the department.

        # Note that some results will have courses unrelated to the department.
        # For example, a department code of 'EG' will have course code results
        # of 'ENGL', 'ENE', etc. For data integrity, this is filtered.
        course_rel_urls = []
        department_url = urljoin(Textbooks.host, relative_url)
        soup = Textbooks.scraper.http_request(
            department_url,
            params=dict(q=department),
        )

        # Use regex to filter textbooks having the right department substring.
        regex = department + '[0-9]+'

        # Filter to only retain one department code of courses.
        courses_all = soup.find_all('h3')
        courses = [c for c in courses_all if re.search(regex, c.text)]

        Textbooks.logger.debug('%s course(s) found', len(courses))

        for course in courses:
            try:
                course_rel_url = None
                siblings = (
                    sib for sib in course.next_siblings if isinstance(sib, Tag)
                )

                # Traverse course's siblings until we bump into its URL tag.
                for sib in siblings:
                    if course_rel_url:
                        break

                    course_rel_url = sib.find('dd', text=re.compile('Course='))

                if course_rel_url:
                    course_rel_urls.append(course_rel_url.text.strip())

            except Exception:
                Textbooks.scraper.handle_error()

        return course_rel_urls

    @staticmethod
    def _get_course_page(course_rel_url):
        # Get HTML of course webpage given a course relative URL.
        course_url = urljoin(Textbooks.host, course_rel_url)
        soup = Textbooks.scraper.http_request(course_url)

        return soup, course_url

    @staticmethod
    def _parse_course_data(course_page, course_url):
        # Parse course data from course page.

        def split_string(string):
            """Separates an alphanumeric string

            E.g: WINTER18 becomes WINTER, [18]
            """

            # NOTE: Some phrases could have multiple hyphens, like
            # 'COMM181-001,-002'. Separate word from num to get
            # ['COMM', '181-001', '-002'], conjoin the 2nd index onwards to
            # one string as '181-001-002', and split again to
            # ['181', '001', '002']. Splice into an array of numbered extras
            # such as ['181-001', '181-002'].
            rgx1, rgx2 = r'([a-zA-Z]+)([0-9]+)', r'\1,\2'

            # Extended Iterable Unpacking (PEP 3132). If too many variables to
            # unpack, the remainder fall under num_raw as an array.
            word, *num_raw = re.sub(rgx1, rgx2, string).split(',')
            num, *extras = ''.join(num_raw).split('-')
            nums = ['-'.join([num, extra]) for extra in extras] or [num]

            return word, nums

        def clean_term(term):
            """Clean parsed term.

            Current known dirty terms:
            - SUM
            - LSUM, LWIN, LSPRING,
            - SPSU
            - FW
            """
            term_map = {
                'WIN': 'Winter',
                'SUM': 'Summer',
                'SPSU': 'Spring,Summer',
                'FW': 'Fall,Winter',
            }

            # Remove leading 'L' from 'LSUM', 'LWIN', etc.
            term = term.lstrip('L')
            return term_map.get(term, term).split(',')

        course_list = []
        regex = re.compile('[()]')

        # E.g.: Course text: ENGL223 (WINTER2018).
        dep_course_code, year_term = course_page.find(
            'span', id='textbookCategory'
            ).text.strip().split(' ')

        # Turns ENGL223 to ENGL and 223.
        department, course_codes = split_string(dep_course_code)

        # Strips '(' and ')' and turns (WINTER2018) into WINTER and 2018.
        # CONT courses have 'CTE' trailing their course codes, such as
        # LWIN18CTE, which is stripped.
        term_raw, year_raw = split_string(
            regex.sub('', year_term).strip('CTE'))

        terms = clean_term(term_raw)
        year = year_raw[0]

        if len(year) == 2:
            year = ''.join(('20', year))

        instructor_raw = course_page.find('a', href=re.compile('people'))

        instructor = ' '.join(
            normalize_string(instructor_raw.text.strip().split(' '))
            if instructor_raw else []
        )

        course_data = {
            'year': year,
            'term': '',
            'department': department,
            'course_code': '',
            'url': course_url,
            'instructor': instructor
        }

        for term in terms:
            for course_code in course_codes:
                course_data.update({
                    'term': term.lower().capitalize(),
                    'course_code': course_code,
                })

                course_list.append(OrderedDict(course_data))

        return course_list

    @staticmethod
    def _parse_textbook_data(textbook):
        # Parse textbook data from course page.

        # ===================== Info retrieved internally =====================
        image_ref = urljoin(
            Textbooks.host,
            textbook.find('img', {'data-id': 'toLoad'})['data-url']
        )
        image_url = Textbooks.scraper.http_request(image_ref, parse=False).text

        status_raw = textbook.find('dd', 'textbookStatus')
        status = status_raw.text.strip() if status_raw else None

        isbn_13 = (
            textbook.find('dt', text=re.compile('ISBN'))
            .next_sibling.next_sibling.text.strip()
        )

        Textbooks.logger.debug('Textbook ISBN: %s', isbn_13)

        # May need both new and old prices, or just new prices (or none).
        prices = textbook.find_all('dd', 'textbookPrice')
        price_new = price_used = None

        if prices:
            if len(prices) > 0 and '$' in prices[0].text:
                price_new = float(prices[0].text.strip().replace(',', '')[1:])

            if len(prices) > 1 and '$' in prices[1].text:
                price_used = float(prices[1].text.strip().replace(',', '')[1:])

        # ========== Info retrieved externally (via Google Books API) =========
        google_books_info = get_google_books_info(isbn_13, Textbooks.scraper)

        if google_books_info:
            title = google_books_info['title']
            authors = google_books_info['authors']
            isbn_10 = google_books_info['isbn_10'][0]
        else:
            title_str = textbook.find(
                'div', class_='textbookInfoHolder').find('h2').text.strip()

            *title_raw, authors_raw = re.sub(
                r'[ ]+by$', ' by ', title_str).split(' by ')

            # Rebuild array name into title. For example, if the title is
            # "Writing by Choice by Eric Henderson", title_raw will
            # be ['Writing, Choice'], and converted into 'Writing by Choice'
            title_combined = ' by '.join(title_raw).strip()

            # Remove whitespace between titles.
            title = re.sub(r'\s+', ' ', title_combined)
            authors = authors_raw.strip().replace('/', ', ').split(', ')
            isbn_10 = None

        # Normalize names, whether from Google Books or Textbooks scraper.
        authors = normalize_string(authors) if authors else []

        data = {
            'id': isbn_13,
            'isbn_10': isbn_10,
            'isbn_13': isbn_13,
            'title': title,
            'authors': authors,
            'image': image_url,
            'price_new': price_new,
            'price_used': price_used,
            'status': status
        }

        return data
