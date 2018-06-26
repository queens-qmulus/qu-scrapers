import re
import requests
import pendulum
import chromedriver_binary # Adds chromedriver_binary to path

from queue import Queue
from urllib.parse import urljoin
from threading import Thread
from collections import OrderedDict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from ..utils import Scraper
from ..utils.config import QUEENS_USERNAME, QUEENS_PASSWORD

from .courses_helpers import (
    setup_logging, save_department_data, save_course_data, save_section_data,
)


class Courses:
    '''
    A scraper for Queen's courses on SOLUS.

    The Courses scraper creates 26 threads, one for each letter, to scrape
    several departments and their courses. It instantiates 26 Course workers,
    each of which creates a course session that handles a SOLUS login to grab
    its credentials via the cookies returned from a login.
    '''

    LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    @staticmethod
    def scrape():
        '''Update database records for courses scraper'''

        logger = setup_logging()

        logger.info('Starting Courses scrape')
        queue = Queue()

        for _ in Courses.LETTERS:
            course_worker = CourseWorker(queue)
            course_worker.daemon = True
            course_worker.start()

        for letter in Courses.LETTERS:
            queue.put(letter)

        queue.join()
        logger.info('Completed Courses scrape')

class CourseWorker(Thread):
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            letter = self.queue.get()
            course_scraper = CourseSession()
            course_scraper.scrape(letter)
            self.queue.task_done()

class CourseSession:
    """A scraper for Queen's courses"""

    host = 'https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.SSS_BROWSE_CATLG_P.GBL'

    def __init__(self, location='./dumps/courses'):
        self.scraper = Scraper()
        self.location = location
        self.logger = self.scraper.logger
        self.cookies = self._login()

    def scrape(self, letter):
        soup = self._request_page()
        departments = self._get_departments(soup, letter)

        self.logger.debug('Letter {} has {} depts.'.format(letter, len(departments)))

        # For each department under a certain letter search
        for department in departments:
            try:
                dept_data = self._parse_department_data(department)
                save_department_data(dept_data, self.scraper, self.location)

                courses = department.find_all('tr', id=re.compile('trCOURSE_LIST'))

                # For each course under a certain department
                for course in courses:
                    return_state = 'DERIVED_SAA_CRS_RETURN_PB$163$'

                    try:
                        course_number = course.find('a', id=re.compile('CRSE_NBR\$'))['id']
                        course_name = course.find('span', id=re.compile('CRSE_TITLE\$')).text

                        if not course_number:
                            self.logger.debug('Course number does not exist. Skipping')
                            continue

                        if 'unspecified' in course_name.lower():
                            self.logger.debug('Skipping unspecified course')
                            continue

                        # Note: Selecting course only takes one parameter, which is the ICAction
                        ic_action = {'ICAction': course_number}
                        soup = self._request_page(ic_action)

                        # Some courses have multiple offerings of the same course
                        # E.g: MATH121 offered on campus and online. Check if
                        # table representing academic levels exists
                        if not self._has_multiple_course_offerings(soup):
                            title = soup.find('span', id='DERIVED_CRSECAT_DESCR200').text.strip()
                            self.logger.debug('Course title: {}'.format(title))
                            self.logger.debug('Only one course offering here. Parsing course data')

                            self._navigate_and_parse_course(soup)
                        else:
                            return_state = 'DERIVED_SSS_SEL_RETURN_PB$181$'
                            title = soup.find('span', id='DERIVED_SSS_SEL_DESCR200').text.strip()
                            self.logger.debug('Course title: {}'.format(title))
                            self.logger.debug('** THIS HAS MULITPLE COURSE OFFERINGS **')

                            academic_levels = self._get_academic_levels(soup)

                            for academic_level in academic_levels:
                                try:
                                    career_number = academic_level['id']
                                    career_name = academic_level.text.strip()
                                    self.logger.debug('Getting career: {}'.format(career_name))

                                    # go from a certain academic level to basic course page
                                    ic_action = {'ICAction': career_number}

                                    soup = self._request_page(ic_action)
                                    self._navigate_and_parse_course(soup)

                                except Exception as ex:
                                    self.scraper.handle_error(ex, 'scrape_inner')

                            self.logger.debug('Done careers.')

                    except Exception as ex:
                        self.scraper.handle_error(ex, 'scrape_middle')

                    # go back to course listing
                    self.logger.debug('Returning to course list')
                    ic_action = {'ICAction': return_state}
                    self._request_page(ic_action)

                self.logger.debug('Done department')

            except Exception as ex:
                self.scraper.handle_error(ex, 'scrape_outer')

        self.logger.debug('Done letter {}'.format(letter))

    def _navigate_and_parse_course(self, soup):
        try:
            # course parse
            course_data = self._parse_course_data(soup)
            save_course_data(course_data, self.scraper, self.location)

            # section(s) parse
            if not self._has_course_sections(soup):
                self.logger.debug('No course sections. Skipping deep scrape')
            else:
                # go to sections page
                ic_action = {'ICAction': 'DERIVED_SAA_CRS_SSR_PB_GO'}
                soup = self._request_page(ic_action)

                terms = soup.find('select', id='DERIVED_SAA_CRS_TERM_ALT').find_all('option')

                self.logger.debug('{} terms available.'.format(len(terms)))

                for term in terms:
                    try:
                        term_number = int(term['value'])
                        self.logger.debug('Starting term: {} ({})'.format(term.text.strip(), term_number))

                        payload = {
                            'ICAction': 'DERIVED_SAA_CRS_SSR_PB_GO$3$',
                            'DERIVED_SAA_CRS_TERM_ALT': term_number,
                            }

                        soup = self._request_page(payload)

                        # view all sections
                        # NOTE: PeopleSoft maintains state of 'View All' for sections
                        # per every other new section you select. This means it
                        # only needs to be expanded ONCE.
                        if self._is_view_sections_closed(soup):
                            self.logger.debug("'View All' tab is minimized. Requesting 'View All' for current term...")
                            payload.update({'ICAction': 'CLASS_TBL_VW5$hviewall$0'})
                            soup = self._request_page(payload)
                            self.logger.debug("'View All' request complete.")

                        sections = self._get_sections(soup)

                        self.logger.debug('Total sections: {}'.format(len(sections)))

                        for section in sections:
                            try:
                                section_name = soup.find('a', id=section).text.strip().split(' ')[0]
                                self.logger.debug('Section name: {}'.format(section_name))

                                # go to sections page.
                                payload.update({'ICAction': section})
                                section_soup = self._request_page(payload)
                                course_section_base_data, course_section_data = self._parse_course_section_data(section_soup, course_data, section_name)

                                save_section_data(
                                    course_section_base_data,
                                    course_section_data,
                                    self.scraper,
                                    self.location
                                )

                            except Exception as ex:
                                self.scraper.handle_error(ex, '_navigate_and_parse_course_inner')

                            # go back to sections.
                            ic_action = {'ICAction': 'CLASS_SRCH_WRK2_SSR_PB_CLOSE'}
                            self._request_page(ic_action)

                        self.logger.debug('Done term')

                    except Exception as ex:
                        self.scraper.handle_error(ex, '_navigate_and_parse_course_middle')

                self.logger.debug('Done course')

        except Exception as ex:
            self.scraper.handle_error(ex, '_navigate_and_parse_course_outer')

        ic_action = {'ICAction': 'DERIVED_SAA_CRS_RETURN_PB$163$'}
        self._request_page(ic_action)

    def _login(self):
        '''
        Emulate a SOLUS login via a Selenium webdriver. Mainly used for user
        authentication. Returns session cookies, which are retrieved and used
        for the remainder of this scraping session.

        Returns:
            Object
        '''

        def run_selenium_routine(func):
            while True:
                try:
                    return func()
                except Exception as ex:
                    self.logger.error(
                        'Selenium failure: {}'.format(ex), exc_info=True)

                    continue

        self.logger.info('Running webdriver for authentication...')

        chrome_options = Options()

        # prevent images from loading
        prefs = {'profile.managed_default_content_settings.images': 2}

        chrome_options.add_argument('--headless')
        chrome_options.add_experimental_option('prefs', prefs)

        driver = webdriver.Chrome(chrome_options=chrome_options)

        # timeout to for an element to be found
        driver.implicitly_wait(30)
        driver.set_page_load_timeout(30)
        driver.get('https://my.queensu.ca')

        # sometimes, Selenium errors out when searching for certain fields.
        # retry this routines until it succeeds.
        run_selenium_routine(
            lambda: driver.find_element_by_id('username').send_keys(
                QUEENS_USERNAME
            )
        )

        run_selenium_routine(
            lambda: driver.find_element_by_id('password').send_keys(
                QUEENS_PASSWORD
            )
        )

        run_selenium_routine(
            lambda: driver.find_element_by_class_name('form-button').click()
        )

        run_selenium_routine(
            lambda: driver.find_element_by_class_name('solus-tab').click()
        )

        iframe = run_selenium_routine(
            lambda: driver.find_element_by_id('ptifrmtgtframe')
        )

        driver.switch_to_frame(iframe)

        run_selenium_routine(
            lambda: driver.find_element_by_link_text('Search').click()
        )

        session_cookies = {}

        for cookie in driver.get_cookies():
            session_cookies[cookie['name']] = cookie['value']

        driver.close()

        self.logger.info('Webdriver authentication complete')

        return session_cookies

    def _request_page(self, params=None):
        return self.scraper.http_request(
            url=self.host,
            params=params,
            cookies=self.cookies
        )

    def _get_hidden_params(self, soup):
        '''
        Parses HTML for hidden values that represent SOLUS parameters. SOLUS
        uses dynamic parameters to represent user state given certain actions
        taken.

        Returns:
            Object
        '''

        params = {}
        hidden = soup.find('div', id=re.compile('win\ddivPSHIDDENFIELDS'))

        if not hidden:
            hidden = soup.find(
                'field', id=re.compile('win\ddivPSHIDDENFIELDS'))

        params.update({
            x.get('name'): x.get('value') for x in hidden.find_all('input')
        })

        return params

    def _get_departments(self, soup, letter):
        """Click and expand a certain letter to see departments
        E.G: 'A' has AGHE, ANAT, 'B' has BIOL, BCMP, etc
        """
        def update_params_and_make_request(soup, ic_action):
            payload = self._get_hidden_params(soup)
            payload.update(ic_action)

            soup = self._request_page(payload)
            return soup

        # Get all departments for a certain letter
        ic_action = {'ICAction': 'DERIVED_SSS_BCC_SSR_ALPHANUM_{}'.format(letter)}
        soup = update_params_and_make_request(soup, ic_action)

        # Expand all department courses
        ic_action = {'ICAction': 'DERIVED_SSS_BCC_SSS_EXPAND_ALL$97$'}
        soup = update_params_and_make_request(soup, ic_action)

        departments = soup.find_all(
            'table', id=re.compile('ACE_DERIVED_SSS_BCC_GROUP_BOX_1')
        )

        return departments

    def _get_sections(self, soup):
        return [sec['id'] for sec in soup.find_all(
            'a', id=re.compile('CLASS_SECTION\$'))]

    def _on_course_list(self, soup):
        return soup.find('span', id='DERIVED_REGFRM1_TITLE1')

    def _has_multiple_course_offerings(self, soup):
        return soup.find('table', id='CRSE_OFFERINGS$scroll$0')

    def _has_course_sections(self, soup):
        return soup.find('input', id='DERIVED_SAA_CRS_SSR_PB_GO')

    def _is_view_sections_closed(self, soup):
        view_all_tab = soup.find('a', id='CLASS_TBL_VW5$hviewall$0')
        return view_all_tab and 'View All' in view_all_tab

    def _get_academic_levels(self, soup):
        return [url for url in soup.find_all('a', id=re.compile('CAREER\$'))]

    def _parse_department_data(self, department):
        REGEX_TITLE = re.compile('DERIVED_SSS_BCC_GROUP_BOX_1\$147\$\$span\$')
        dept_str = department.find('span', id=REGEX_TITLE).text.strip()

        self.logger.debug('Department: {name}'.format(name=dept_str))

        # Some departments have more than one hypen such as
        # "MEI - Entrepreneur & Innov - Masters". Find first index of '-' to
        # split code from name.
        name_index = dept_str.find('-')
        code = dept_str[:name_index].strip()
        name = dept_str[name_index + 2:].strip()

        data = {
            'code': code,
            'name': name,
        }

        return data

    def _parse_course_data(self, soup):
        # All HTML id's used via regular expressions
        REGEX_TITLE = re.compile('DERIVED_CRSECAT_DESCR200')
        REGEX_CAMPUS = re.compile('CAMPUS_TBL_DESCR')
        REGEX_DESC = re.compile('SSR_CRSE_OFF_VW_DESCRLONG')
        REGEX_UNITS = re.compile('DERIVED_CRSECAT_UNITS_RANGE')
        REGEX_BASIS = re.compile('SSR_CRSE_OFF_VW_GRADING_BASIS')
        REGEX_AC_LVL = re.compile('SSR_CRSE_OFF_VW_ACAD_CAREER')
        REGEX_AC_GRP = re.compile('ACAD_GROUP_TBL_DESCR')
        REGEX_AC_ORG = re.compile('ACAD_ORG_TBL_DESCR')
        REGEX_CRSE_CMPS  = re.compile('ACE_SSR_DUMMY_RECVW')
        REGEX_ENROLL_TBL = re.compile('ACE_DERIVED_CRSECAT_SSR_GROUP2')
        REGEX_ENROLL_DIV = re.compile('win0div')
        REGEX_CEAB = re.compile('ACE_DERIVED_CLSRCH')

        def filter_course_name(soup):
            course_title = soup.find('span', id=REGEX_TITLE).text.strip()
            name_index = course_title.find('-')

            dept_raw, course_code_raw = course_title[:name_index - 1].split(' ')
            course_name = course_title[name_index + 1:].strip()

            dept = dept_raw.encode('ascii', 'ignore').decode().strip()
            course_code = course_code_raw.encode('ascii', 'ignore').decode().strip()

            return dept, course_code, course_name

        def filter_description(soup):
            # TODO: Filter different text sections from description, such as
            # 'NOTE', 'LEARNING HOURS', etc
            descr_raw = soup.find('span', id=REGEX_DESC)

            if not descr_raw:
                return ''

            # If <br/> tags exist, there will be additional information other
            # than the description. Filter for description only.
            if descr_raw.find_all('br'):
                return descr_raw.find_all('br')[0].previous_sibling

            return descr_raw.text.encode('ascii', 'ignore').decode().strip()

        def create_dict(rows, tag, tag_id=None, start=0, enroll=False):
            ENROLLMENT_INFO_MAP = {
                'Enrollment Requirement': 'requirements',
                'Add Consent': 'add_consent',
                'Drop Consent': 'drop_consent',
                }

            data = {}

            for row in rows:
                name_raw, desc_raw = row.find_all(tag, id=tag_id)[start:]
                name = name_raw.text.strip()
                desc = desc_raw.text.encode('ascii', 'ignore').decode().strip()

                if enroll:
                    name = ENROLLMENT_INFO_MAP[name]
                else:
                    name = name.lower().replace(' / ', '_')

                data.update({name: desc})

            return data

        def create_ceab_dict(soup):
            CEAB_MAP = {
                'Basic Sci': 'basic_sci',
                'Comp St': 'comp_st',
                'End Des': 'end_des',
                'Eng Sci': 'eng_sci',
                'Math': 'math',
                }

            ceab_data = {}
            ceab_units = (
                soup
                    .find('table', id=REGEX_CEAB) # CEAB table
                    .find_all('tr')[1]  # data is only in 2nd row
                    .find_all('td')[1:] # first cell is metadata
                )

            # Iteration by twos. Format: Name, Units
            for i in range(0, len(ceab_units), 2):
                name = ceab_units[i].text.strip().strip(':')
                units = ceab_units[i + 1].text.strip().strip(':')

                ceab_data.update({CEAB_MAP[name]: float(units) if units else 0})

            return ceab_data

        department, course_code, course_name = filter_course_name(soup)

        # =========================== Course Detail ===========================
        academic_level = soup.find('span', id=REGEX_AC_LVL).text.strip()

        # Note: Anomaly scenario of LAW 696 having a range of units, such as
        # "2.00 - 8.00". This is handled by splitting and taking the larger
        # number.
        units = float(soup.find('span', id=REGEX_UNITS).text.strip().split(' - ')[-1])
        grading_basis = soup.find('span', id=REGEX_BASIS).text.strip()
        academic_group = soup.find('span', id=REGEX_AC_GRP).text.strip()
        academic_org = soup.find('span', id=REGEX_AC_ORG).text.strip()

        # some sections have no campus listed
        campus_raw = soup.find('span', id=REGEX_CAMPUS)
        campus = campus_raw.text.strip() if campus_raw else 'None'

        # course_components is a dict of data
        course_components_rows = soup.find('table', id=REGEX_CRSE_CMPS).find_all('tr')[1:]
        course_components = create_dict(course_components_rows, 'td', start=1)

        # Note: The following fields potentially could be missing data

        # ======================= Enrollment Information ======================
        enrollment_table =  soup.find('table', id=REGEX_ENROLL_TBL)
        enrollment_info_rows = enrollment_table.find_all('tr')[1:] if enrollment_table else []

        # Will not exist for 2nd half of full-year courses, like MATH 121B
        enroll_info = create_dict(enrollment_info_rows, 'div', tag_id=REGEX_ENROLL_DIV, enroll=True)

        # ============================ Description ============================
        description = filter_description(soup)

        # ============================ CEAB Units =============================
        ceab_data = create_ceab_dict(soup)

        data = {
            'department': department,
            'course_code': course_code,
            'course_name': course_name,
            'campus': campus,
            'description': description,
            'grading_basis': grading_basis,
            'course_components': course_components,
            'requirements': enroll_info.get('requirements', ''),
            'add_consent': enroll_info.get('add_consent', ''),
            'drop_consent': enroll_info.get('drop_consent', ''),
            'academic_level': academic_level,
            'academic_group': academic_group,
            'academic_org': academic_org,
            'units': units,
            'CEAB': ceab_data,
            }

        # retain key-value order of dictionary
        return OrderedDict(data)

    def _parse_course_section_data(self, soup, basic_data, section_name):
        DAY_MAP = {
            'Mo': 'Monday',
            'Tu': 'Tuesday',
            'We': 'Wednesday',
            'Th': 'Thursday',
            'Fr': 'Friday',
            'Sa': 'Saturday',
            'Su': 'Sunday',
            }

        # =========================== Class Details ===========================
        section_name = section_name
        _, year_term, section_type = soup.find('span', id='DERIVED_CLSRCH_SSS_PAGE_KEYDESCR').text.strip().split(' | ')
        section_type = section_type.replace(' ', '') # trims spaces in 'Lecture / Discussion'
        year, term = year_term.split(' ')
        section_number = soup.find('span', id='DERIVED_CLSRCH_DESCR200').text.strip().split(' - ')[1][:3]
        class_number = int(soup.find('span', id='SSR_CLS_DTL_WRK_CLASS_NBR').text.strip())

        # Note: There are start/end dates for the COURSE, and start/end dates
        # for a section. These two start/end date variables are for the course
        # (may not be necessary)

        # ISO 8601 date format
        course_start_date, course_end_date = [pendulum.parse(date, strict=False).isoformat().split('T')[0] for date in soup.find('span', id='SSR_CLS_DTL_WRK_SSR_DATE_LONG').text.strip().split(' - ')]

        # ======================== Meeting Information ========================
        course_dates = []

        # see how many rows of class times there are
        date_rows = soup.find_all('tr', id=re.compile('trSSR_CLSRCH_MTG\$[0-9]+_row'))

        # Note: Some rows have dates such as "MoTu 9:30AM - 10:30AM"
        for date_row in date_rows:
            days = []

            # some (incorrect) sections will have a missing day, such as a
            # listing like "12:00AM - 12:00AM" instead of "Mo 8:30AM - 9:30AM"
            # filter out hyphen to ensure the ordering of start/end indices
            # are consistent
            date_times = date_row.find(
                'span', id=re.compile('MTG_SCHED\$')
            ).text.strip().replace(' - ', ' ').split(' ')

            if 'TBA' in date_times:
                start_time = end_time = 'TBA'
            else:
                # No day is listed. Mark as null
                day_str = date_times[0] if len(date_times) > 2 else 'n/a'

                start_time = pendulum.parse(date_times[-2], strict=False).isoformat().split('T')[1][:5]
                end_time = pendulum.parse(date_times[-1], strict=False).isoformat().split('T')[1][:5]

                for day_short, day_long in DAY_MAP.items():
                    if day_short in day_str:
                        days.append(day_long)

                # If no day_str exists, mark day as n/a to be flagged later
                if not days:
                    days.append(day_str)

            location = soup.find('span', id=re.compile('MTG_LOC\$')).text.strip()
            instructors_raw = soup.find('span', id=re.compile('MTG_INSTR\$')).text.strip().split(', \r')

            # turn "Last,First" into "Last, First"
            instructors = [ins.replace(',', ', ') for ins in instructors_raw]

            # start/end dates for a partcular SECTION
            meeting_dates = soup.find('span', id=re.compile('MTG_DATE\$')).text.strip().split(' - ')

            if 'TBA' in meeting_dates:
                start_date = end_date = 'TBA'
            else:
                start_date, end_date = [
                    pendulum.parse(date, strict=False).isoformat().split('T')[0] for date in
                        soup.find('span', id=re.compile('MTG_DATE\$')).text.strip().split(' - ')
                    ]

            course_date = {
                'day': 'TBA' if 'TBA' in date_times else None,
                'start_time': start_time,
                'end_time': end_time,
                'start_date': start_date,
                'end_date': end_date,
                'location': location,
                'instructors': instructors,
                }

            if course_date['day'] == 'TBA':
                course_dates.append(OrderedDict(course_date))
            else:
                for day in days:
                    # flag non-existent day as empty string
                    course_date['day'] = '' if day == 'n/a' else day
                    course_dates.append(OrderedDict(course_date))

        # ========================= Class Availability ========================
        enrollment_capacity = int(soup.find('div', id='win0divSSR_CLS_DTL_WRK_ENRL_CAP').text.strip())
        enrollment_total = int(soup.find('div', id='win0divSSR_CLS_DTL_WRK_ENRL_TOT').text.strip())
        waitlist_capacity = int(soup.find('div', id='win0divSSR_CLS_DTL_WRK_WAIT_CAP').text.strip())
        waitlist_total = int(soup.find('div', id='win0divSSR_CLS_DTL_WRK_WAIT_TOT').text.strip())

        # ========================== Combined Section =========================
        combined_with = []

        combined_rows = soup.find_all('tr', id=re.compile('trSCTN_CMBND\$[0-9]+_row')) or []

        for combined_row in combined_rows:
            combined_section_number = int(combined_row.find('span', id=re.compile('CLASS_NAME\$')).text.split('(')[1][:-1])

            if combined_section_number != class_number:
                combined_with.append(combined_section_number)

        section_data = {
            'section_name:': section_name,
            'section_type:': section_type,
            'section_number:': section_number,
            'class_number': class_number,
            'dates:': course_dates,
            'combined_with:': combined_with,
            'enrollment_capacity:': enrollment_capacity,
            'enrollment_total:': enrollment_total,
            'waitlist_capacity:': waitlist_capacity,
            'waitlist_total:': waitlist_total,
            'last_updated:': pendulum.now().isoformat(),
            }

        course_data = {
            'year': year,
            'term': term,
            'department': basic_data.get('department', ''),
            'course_code': basic_data.get('course_code', ''),
            'course_name': basic_data.get('course_name', ''),
            'units': basic_data.get('units', ''),
            'campus': basic_data.get('campus', ''),
            'academic_level': basic_data.get('academic_level', ''),
            }

        return OrderedDict(course_data), OrderedDict(section_data)
