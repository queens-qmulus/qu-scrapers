import re
import socket
import chromedriver_binary # Adds chromedriver_binary to path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from urllib.parse import urljoin
from collections import OrderedDict

from ..utils import Scraper
from ..utils.config import QUEENS_USERNAME, QUEENS_PASSWORD
from .courses_helpers import noop

class Courses:
    '''
    A scraper for Queen's courses.
    '''

    host = 'https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.SSS_BROWSE_CATLG_P.GBL'
    LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    headers = {
        'Pragma': 'no-cache',
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Accept-Language': 'en-US,en;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
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
    def scrape():
        '''Update database records for courses scraper'''

        params = {}
        params.update(Courses.START_PARAMS)

        print('Starting Courses scrape')

        # Imitate an actual login and grab generated cookies, which allows the
        # bypass of SOLUS request redirects.
        cookies = Courses._login()

        # TODO: Should be GET (it is)
        soup = Courses._request_page(params, cookies)

        hidden_params = Courses._get_hidden_params(soup)
        params.update(hidden_params)
        params.update(Courses.AJAX_PARAMS)

        # Click and expand a certain letter to see departments
        # E.G: 'A': has AGHE, ANAT... 'B' has BIOL, BCMP..., etc
        for dept_letter in Courses.LETTERS[12]: # Status: Verified, temporary
            try:
                departments = Courses._get_departments(
                    soup, dept_letter, params, cookies
                    )

                print('Got departments. Parsing each department')

                # For each department under a certain letter search
                for department in departments[1:]: # Status: Verified, temporary
                    try:
                        dept_name = department.find(
                            'span',
                            id=re.compile('DERIVED_SSS_BCC_GROUP_BOX_1\$147\$\$span\$')
                            ).text.strip()

                        name_index = dept_name.find('-')
                        dept_code = dept_name[:name_index].strip()

                        print('Department: {name}'.format(name=dept_name))
                        print('==============================================')

                        courses = Courses._get_courses(department)

                        # For each course under a certain department
                        for course in courses: # Status: Verified
                            try:
                                course_soup_rows = course.find_all('td')

                                course_number = course_soup_rows[1].find('a')['id']
                                course_code = course_soup_rows[1].find('a').text.strip()
                                course_name = course_soup_rows[2].find('a').text.strip()

                                print('({num}) {dept} {code}: {name}'.format(
                                    num=course_number,
                                    dept=dept_code,
                                    code=course_code,
                                    name=course_name,
                                    ))

                                if 'unspecified' in course_name.lower():
                                    print('Skipping unspecified course')
                                    continue

                                # TODO: Should be POST (it isn't)
                                # Note: Selecting course only takes one parameter, which
                                # is the ICAction
                                ic_action = {'ICAction': course_number}
                                soup = Courses._request_page(ic_action, cookies)

                                # Some courses have multiple offerings of the same course
                                # E.g: MATH121 offered on campus and online. Check if
                                # table representing academic levels exists
                                # Status: Verified
                                if Courses._has_multiple_course_offerings(soup):
                                    print('** THIS HAS MULITPLE COURSE OFFERINGS **')

                                    academic_levels = Courses._get_academic_levels(soup)

                                    for career_number in academic_levels:
                                        try:
                                            ic_action = {'ICAction': career_number}
                                            soup = Courses._request_page(ic_action, cookies)
                                            course_info = Courses._parse_course_data(soup)

                                            print('Returning to career selection...')

                                            # go back to academic level choices page
                                            ic_action = {'ICAction': 'DERIVED_SAA_CRS_RETURN_PB$163$'}
                                            Courses._request_page(ic_action, cookies)

                                            Scraper.save_data(course_info, 'courses')

                                        except Exception as ex:
                                            Scraper.handle_error(ex, 'scrape')

                                     # go back to course listing
                                    print('Done careers. Returning to course list')
                                    ic_action = {'ICAction': 'DERIVED_SSS_SEL_RETURN_PB$181$'}
                                    Courses._request_page(ic_action, cookies)
                                else:
                                    course_info = Courses._parse_course_data(soup)
                                    Scraper.save_data(course_info, 'courses')

                                     # go back to course listing
                                    print('Done single course. Returning to course list')
                                    ic_action = {'ICAction': 'DERIVED_SAA_CRS_RETURN_PB$163$'}
                                    Courses._request_page(ic_action, cookies)


                            except Exception as ex:
                                Scraper.handle_error(ex, 'scrape')

                        print('\nDone departments')
                        break # temporary

                    except Exception as ex:
                        Scraper.handle_error(ex, 'scrape')

                break # temporary

            except Exception as ex:
                Scraper.handle_error(ex, 'scrape')

            break # temporary

        print('\nShallow course scrape complete')


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
        # socket.setdefaulttimeout(60) # timeout for current socket in use

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
    def _request_page(params, cookies):
        return Scraper.http_request(
            Courses.host,
            params=params,
            cookies=cookies
            )

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
                'field', id=re.compile('win\ddivPSHIDDENFIELDS')
                )

        params.update({
            x.get('name'): x.get('value') for x in hidden.find_all('input')
            })

        return params


    # Currently not in use
    @staticmethod
    def _get_ptus_params(soup):
        params = {}
        ptus_list = soup.find_all('input', id=re.compile('ptus'))

        params.update({
            x.get('name'): x.get('value') for x in ptus_list
            })

        return params

    # Currently not in use
    @staticmethod
    def _remove_params(params, params_keys):
        return {
            key: val for key, val in params.items()
                if key not in params_keys
            }


    # Status: Verified
    @staticmethod
    def _get_departments(soup, letter, params, cookies):
        def update_params_and_make_request(soup, payload, cookies, ic_action):
            payload = Courses._get_hidden_params(soup)
            payload.update(ic_action)

            # TODO: Should be POST (it isn't)
            soup = Courses._request_page(payload, cookies)
            Scraper.wait()

            return soup

        # Get all departments for a certain letter
        ic_action = {'ICAction': 'DERIVED_SSS_BCC_SSR_ALPHANUM_{}'.format(letter)}
        soup = update_params_and_make_request(soup, params, cookies, ic_action)

        # Expand all department courses
        ic_action = {'ICAction': 'DERIVED_SSS_BCC_SSS_EXPAND_ALL$97$'}
        soup = update_params_and_make_request(soup, params, cookies, ic_action)

        departments = soup.find_all(
            'table', id=re.compile('ACE_DERIVED_SSS_BCC_GROUP_BOX_1')
            )

        return departments

    # Status: Verified
    @staticmethod
    def _get_courses(department_soup):
        return department_soup.find_all('tr', id=re.compile('trCOURSE_LIST'))


    @staticmethod
    def _has_multiple_course_offerings(soup):
        return soup.find('table', id='CRSE_OFFERINGS$scroll$0')


    @staticmethod
    def _get_academic_levels(soup):
        return [
            a['id'] for a in soup.find_all('a', id=re.compile('CAREER\$'))
            ]

    # Status: Verified
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
            # TODO: Figure out way to filter for  'NOTE', 'LEARNING HOURS', etc
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

        # === Course Detail information ===
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

        # === Enrollment information ===
        enrollment_table =  soup.find('table', id=REGEX_ENROLL_TBL)
        enrollment_info_rows = enrollment_table.find_all('tr')[1:] if enrollment_table else []

        # Will not exist for 2nd half of full-year courses, like MATH 121B
        enroll_info = create_dict(enrollment_info_rows, 'div', tag_id=REGEX_ENROLL_DIV, enroll=True)

        # === Description Informaiton ===
        description = filter_description(soup)

        # === CEAB Units ===
        ceab_data = create_ceab_dict(soup)

        data = {
            # NOTE: course_id not shown on generic course page. Must do deep
            # scrape of course sections for course_id
            'course_id': None,
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

