import re
import pendulum
import chromedriver_binary # Adds chromedriver_binary to path

from urllib.parse import urljoin
from collections import OrderedDict

from pymongo import MongoClient

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from ..utils import Scraper
from ..utils.config import QUEENS_USERNAME, QUEENS_PASSWORD
from .courses_helpers import (
    save_department_data,
    save_course_data,
    save_section_data,
)


class Courses:
    '''
    A scraper for Queen's courses.
    '''

    host = 'https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.SSS_BROWSE_CATLG_P.GBL'
    LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Accept-Language': 'en-US,en;q=0.8',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
        'Referer': 'https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.CLASS_SEARCH.GBL?Page=SSR_CLSRCH_ENTRY&Action=U',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        }

    START_PARAMS = {
        'Page': 'SSS_BROWSE_CATLG',
        'Action': 'U',
        }

    AJAX_PARAMS = {
        'ICAJAX': '1',
        'ICNAVTYPEDROPDOWN': '1'
        }

    @staticmethod
    def scrape(location='./dumps/courses'):
        '''Update database records for courses scraper'''

        params = {}
        params.update(Courses.START_PARAMS)

        # Imitate an actual login and grab generated cookies, which allows the
        # bypass of SOLUS request redirects.
        Courses.cookies = Courses._login()

        # TODO: Should be GET (it is)
        soup = Courses._request_page(params)

        hidden_params = Courses._get_hidden_params(soup)
        params.update(hidden_params)
        params.update(Courses.AJAX_PARAMS)

        # Click and expand a certain letter to see departments
        # E.G: 'A' has AGHE, ANAT, 'B' has BIOL, BCMP, etc
        for dept_letter in Courses.LETTERS:
            try:
                departments = Courses._get_departments(
                    soup, dept_letter, params
                )

                print('Got departments. Parsing each department')

                # For each department under a certain letter search
                for department in departments:
                    try:
                        dept_data = Courses._parse_department_data(department)
                        save_department_data(dept_data, location)

                        courses = department.find_all('tr', id=re.compile('trCOURSE_LIST'))

                        # For each course under a certain department
                        for course in courses:
                            return_state = 'DERIVED_SAA_CRS_RETURN_PB$163$'

                            try:
                                course_number = course.find('a', id=re.compile('CRSE_NBR\$'))['id']
                                course_name = course.find('span', id=re.compile('CRSE_TITLE\$')).text

                                if not course_number:
                                    print('Course number does not exist. Skipping')
                                    continue

                                if 'unspecified' in course_name.lower():
                                    print('Skipping unspecified course')
                                    continue

                                # TODO: Should be POST (it isn't)
                                # Note: Selecting course only takes one parameter, which is the ICAction
                                ic_action = {'ICAction': course_number}
                                soup = Courses._request_page(ic_action)

                                # Some courses have multiple offerings of the same course
                                # E.g: MATH121 offered on campus and online. Check if
                                # table representing academic levels exists
                                if not Courses._has_multiple_course_offerings(soup):
                                    title = soup.find('span', id='DERIVED_CRSECAT_DESCR200').text.strip()
                                    print('{}\n--------------------------------'.format(title))
                                    print('Only one course offering here. Parsing course data')

                                    Courses._navigate_and_parse_course(soup, location)
                                else:
                                    return_state = 'DERIVED_SSS_SEL_RETURN_PB$181$'
                                    title = soup.find('span', id='DERIVED_SSS_SEL_DESCR200').text.strip()
                                    print('{}\n--------------------------------'.format(title))
                                    print('** THIS HAS MULITPLE COURSE OFFERINGS **')

                                    academic_levels = Courses._get_academic_levels(soup)

                                    for academic_level in academic_levels:
                                        try:
                                            career_number = academic_level['id']
                                            career_name = academic_level.text.strip()
                                            print('Getting career: {}'.format(career_name))

                                            # go from a certain academic level to basic course page
                                            ic_action = {'ICAction': career_number}

                                            soup = Courses._request_page(ic_action)
                                            Courses._navigate_and_parse_course(soup, location)

                                        except Exception as ex:
                                            Scraper.handle_error(ex, 'scrape')

                                    print('Done careers.')

                            except Exception as ex:
                                Scraper.handle_error(ex, 'scrape')

                            # go back to course listing
                            print('Returning to course list')
                            ic_action = {'ICAction': return_state}
                            Courses._request_page(ic_action)

                        print('\nDone department')

                    except Exception as ex:
                        Scraper.handle_error(ex, 'scrape')

                print('\nDone letter {}'.format(dept_letter))

            except Exception as ex:
                Scraper.handle_error(ex, 'scrape')

        print('\nCourses scrape complete')

    @staticmethod
    def _navigate_and_parse_course(soup, location):
        try:
            # course parse
            course_data = Courses._parse_course_data(soup)
            save_course_data(course_data, location)

            # section(s) parse
            if not Courses._has_course_sections(soup):
                print('No course sections. Skipping deep scrape')
            else:
                # go to sections page
                ic_action = {'ICAction': 'DERIVED_SAA_CRS_SSR_PB_GO'}
                soup = Courses._request_page(ic_action)

                terms = soup.find('select', id='DERIVED_SAA_CRS_TERM_ALT').find_all('option')

                print('{} terms available.\n'.format(len(terms)))

                for term in terms:
                    try:
                        term_number = int(term['value'])
                        print('Starting term: {} ({})'.format(term.text.strip(), term_number))
                        print('--------------------------------')

                        payload = {
                            'ICAction': 'DERIVED_SAA_CRS_SSR_PB_GO$3$',
                            'DERIVED_SAA_CRS_TERM_ALT': term_number,
                            }

                        soup = Courses._request_page(payload)

                        # view all sections
                        # NOTE: PeopleSoft maintains state of 'View All' for sections
                        # per every other new section you select. This means it
                        # only needs to be expanded ONCE.
                        if Courses._is_view_sections_closed(soup):
                            print("'View All' tab is minimized. Requesting 'View All' for current term...")
                            payload.update({'ICAction': 'CLASS_TBL_VW5$hviewall$0'})
                            soup = Courses._request_page(payload)
                            print("'View All' request complete.")

                        sections = Courses._get_sections(soup)

                        print("Total sections: {}\n".format(len(sections)))

                        for section in sections:
                            try:
                                section_name = soup.find('a', id=section).text.strip().split(' ')[0]
                                print('Section name: {}'.format(section_name))

                                # go to sections page.
                                payload.update({'ICAction': section})
                                section_soup = Courses._request_page(payload)
                                course_section_base_data, course_section_data = Courses._parse_course_section_data(section_soup, course_data, section_name)

                                save_section_data(
                                    course_section_base_data,
                                    course_section_data,
                                    location
                                )

                            except Exception as ex:
                                Scraper.handle_error(ex, '_navigate_and_parse_course')

                            # go back to sections.
                            ic_action = {'ICAction': 'CLASS_SRCH_WRK2_SSR_PB_CLOSE'}
                            Courses._request_page(ic_action)

                        print('Done term\n')

                    except Exception as ex:
                        Scraper.handle_error(ex, '_navigate_and_parse_course')

            print('Done course. Returning to previous page')

        except Exception as ex:
            Scraper.handle_error(ex, '_navigate_and_parse_course')

        ic_action = {'ICAction': 'DERIVED_SAA_CRS_RETURN_PB$163$'}
        Courses._request_page(ic_action)

    @staticmethod
    def _login():
        '''
        Emulate a SOLUS login via a Selenium webdriver. Mainly used for user
        authentication. Returns session cookies, which are retrieved and used
        for the remainder of this scraping session.

        Returns:
            Object
        '''

        print('Running webdriver for authentication...')

        chrome_options = Options()
        chrome_options.add_argument('--headless')

        driver = webdriver.Chrome()
        driver.set_page_load_timeout(30000) # temporary
        driver.implicitly_wait(30000) # temporary, timeout to for an element to be found
        driver.get('https://my.queensu.ca')

        username_field = driver.find_element_by_id('username')
        username_field.clear()
        username_field.send_keys(QUEENS_USERNAME)

        password_field = driver.find_element_by_id('password')
        password_field.clear()
        password_field.send_keys(QUEENS_PASSWORD)

        driver.find_element_by_class_name('form-button').click()
        driver.find_element_by_class_name('solus-tab').click()

        iframe = driver.find_element_by_id('ptifrmtgtframe')

        driver.switch_to_frame(iframe)
        driver.find_element_by_link_text('Search').click()

        session_cookies = {}

        for cookie in driver.get_cookies():
            session_cookies[cookie['name']] = cookie['value']

        driver.close()

        print('Finished with webdriver')

        return session_cookies

    @staticmethod
    def _request_page(params):
        return Scraper.http_request(
            url=Courses.host, params=params, cookies=Courses.cookies)

    @staticmethod
    def _get_hidden_params(soup):
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

    @staticmethod
    def _get_departments(soup, letter, params):
        def update_params_and_make_request(soup, payload, ic_action):
            payload = Courses._get_hidden_params(soup)
            payload.update(ic_action)

            # TODO: Should be POST (it isn't)
            soup = Courses._request_page(payload)
            return soup

        # Get all departments for a certain letter
        ic_action = {'ICAction': 'DERIVED_SSS_BCC_SSR_ALPHANUM_{}'.format(letter)}
        soup = update_params_and_make_request(soup, params, ic_action)

        # Expand all department courses
        ic_action = {'ICAction': 'DERIVED_SSS_BCC_SSS_EXPAND_ALL$97$'}
        soup = update_params_and_make_request(soup, params, ic_action)

        departments = soup.find_all(
            'table', id=re.compile('ACE_DERIVED_SSS_BCC_GROUP_BOX_1')
        )

        return departments

    @staticmethod
    def _get_sections(soup):
        return [sec['id'] for sec in soup.find_all(
            'a', id=re.compile('CLASS_SECTION\$'))]

    @staticmethod
    def _has_multiple_course_offerings(soup):
        return soup.find('table', id='CRSE_OFFERINGS$scroll$0')

    @staticmethod
    def _has_course_sections(soup):
        return soup.find('input', id='DERIVED_SAA_CRS_SSR_PB_GO')

    @staticmethod
    def _is_view_sections_closed(soup):
        view_all_tab = soup.find('a', id='CLASS_TBL_VW5$hviewall$0')
        return view_all_tab and 'View All' in view_all_tab

    @staticmethod
    def _get_academic_levels(soup):
        return [url for url in soup.find_all('a', id=re.compile('CAREER\$'))]

    @staticmethod
    def _parse_department_data(department):
        REGEX_TITLE = re.compile('DERIVED_SSS_BCC_GROUP_BOX_1\$147\$\$span\$')
        dept_str = department.find('span', id=REGEX_TITLE).text.strip()

        print('\nDepartment: {name}'.format(name=dept_str))
        print('==============================================')

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

    @staticmethod
    def _parse_course_data(soup):
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
            # TODO: Figure out way to filter for 'NOTE', 'LEARNING HOURS', etc
            # text sections from description
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
        units = float(soup.find('span', id=REGEX_UNITS).text.strip())
        grading_basis = soup.find('span', id=REGEX_BASIS).text.strip()
        campus = soup.find('span', id=REGEX_CAMPUS).text.strip()
        academic_group = soup.find('span', id=REGEX_AC_GRP).text.strip()
        academic_org = soup.find('span', id=REGEX_AC_ORG).text.strip()

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

    @staticmethod
    def _parse_course_section_data(soup, basic_data, section_name):
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
            date_times = date_row.find('span', id=re.compile('MTG_SCHED\$')).text.strip().split(' ')

            day_str = date_times[0]

            if 'TBA' in date_times:
                start_time = end_time = 'TBA'
            else:
                start_time = pendulum.parse(date_times[1], strict=False).isoformat().split('T')[1][:5]
                end_time = pendulum.parse(date_times[3], strict=False).isoformat().split('T')[1][:5]

                for day_short, day_long in DAY_MAP.items():
                    if day_short in day_str:
                        days.append(day_long)

            location = soup.find('span', id=re.compile('MTG_LOC\$')).text.strip()
            instructors = soup.find('span', id=re.compile('MTG_INSTR\$')).text.strip().split(', \r')

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
                    course_date['day'] = day
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
