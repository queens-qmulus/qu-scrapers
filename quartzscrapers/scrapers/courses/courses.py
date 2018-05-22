import re
import socket
import chromedriver_binary # Adds chromedriver_binary to path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from urllib.parse import urljoin

from ..utils import Scraper
from ..utils.config import QUEENS_USERNAME, QUEENS_PASSWORD
from .courses_helpers import noop


class Courses:
    '''
    A scraper for Queen's courses.
    '''

    host = 'https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.SSS_BROWSE_CATLG_P.GBL' # new
    LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    headers = {
        'Pragma': 'no-cache',
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Accept-Language': 'en-US,en;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.CLASS_SEARCH.GBL?Page=SSR_CLSRCH_ENTRY&Action=U', #new
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
        cookies = Courses.login()

        # TODO: Should be GET (it is)
        soup = Scraper.http_request(
            Courses.host,
            params=params,
            cookies=cookies
            )

        hidden_params = Courses._get_hidden_params(soup)
        params.update(hidden_params)

        # Click and expand a certain letter to see departments
        # E.G: 'A': has AGHE, ANAT... 'B' has BIOL, BCMP..., etc
        for dept_letter in Courses.LETTERS: # Status: Verified
            params.update(Courses.AJAX_PARAMS)

            departments, checkboxes = Courses._get_departments(
                soup, dept_letter, params, cookies
                )

            print('Got departments. Parsing each department')

            # For each department under a certain letter search
            for department in departments: # Status: Verified
                dept_name = department.find(
                    'span',
                    id=re.compile(r'DERIVED_SSS_BCC_GROUP_BOX_1\$147\$\$span\$')
                    ).text.strip()

                name_index = dept_name.find('-')
                dept_code = dept_name[:name_index].strip()

                print('Department: {name}'.format(name=dept_name))
                print('==============================================')

                courses = Courses._get_courses(department)

                # For each course under a certain department
                for course in courses: # Status: Verified
                    course_soup_rows = course.find_all('td')

                    course_number = course_soup_rows[1].find('a')['id']
                    course_code = course_soup_rows[1].find('a').text.strip()
                    course_name = course_soup_rows[2].find('a').text.strip()
                    ic_action = {'ICAction': course_number}

                    print('({num}) {dept} {code}: {name}'.format(
                        num=course_number,
                        dept=dept_code,
                        code=course_code,
                        name=course_name,
                        ))

                    # TODO: Should be POST (it isn't)
                    # Note: Selecting course only takes one parameter, which
                    # is the ICAction
                    base_info = {
                        'department': dept_code,
                        'course_code': course_code,
                        'course_name': course_name,
                        }

                    course_info = Courses._parse_course_data(
                        ic_action,
                        cookies,
                        base_info,
                        )

                print('\n')

        print('\nShallow course scrape complete')


    @staticmethod
    def login():
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

        # TODO: Change timeout back to default

        driver = webdriver.Chrome()
        driver.set_page_load_timeout(30000)
        driver.implicitly_wait(30000) # timeout to for an element to be found
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
    def _get_hidden_params(soup):
        '''
        Parses HTML for hidden values that represent SOLUS parameters. SOLUS
        uses dynamic parameters to represent user state given certain actions
        taken.

        Returns:
            Object
        '''

        params = {}
        hidden = soup.find('div', id=re.compile(r'win\ddivPSHIDDENFIELDS'))

        if not hidden:
            hidden = soup.find(
                'field', id=re.compile(r'win\ddivPSHIDDENFIELDS')
                )

        params.update({
            x.get('name'): x.get('value') for x in hidden.find_all('input')
            })

        return params


    # Currently not in use
    @staticmethod
    def _get_ptus_params(soup):
        params = {}
        ptus_list = soup.find_all('input', id=re.compile(r'ptus'))

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
            soup = Scraper.http_request(
                Courses.host,
                params=payload,
                cookies=cookies,
                )

            Scraper.wait()

            return soup

        # Get all departments for a certain letter
        ic_action = {'ICAction': 'DERIVED_SSS_BCC_SSR_ALPHANUM_{}'.format(letter)}
        soup = update_params_and_make_request(soup, params, cookies, ic_action)

        # Expand all department courses
        ic_action = {'ICAction': 'DERIVED_SSS_BCC_SSS_EXPAND_ALL$97$'}
        soup = update_params_and_make_request(soup, params, cookies, ic_action)

        departments = soup.find_all(
            'table', id=re.compile(r'ACE_DERIVED_SSS_BCC_GROUP_BOX_1')
            )

        checkboxes = soup.find_all(
            'input', id=re.compile(r'CRSE_SEL_CHECKBOX\$chk\$')
            )

        return departments, checkboxes


    # Status: Verified
    @staticmethod
    def _get_courses(department_soup):
        return department_soup.find_all('tr', id=re.compile(r'trCOURSE_LIST'))


    # Status: Pending
    @staticmethod
    def _parse_course_data(ic_action, cookies, base_info):
        ENROLLMENT_INFO_MAP = {
            'Enrollment Requirement': 'requirements',
            'Add Consent': 'add_consent',
            'Drop Consent': 'drop_consent',
            }

        soup = Scraper.http_request(
            Courses.host,
            params=ic_action,
            cookies=cookies
            )

        description = soup.find('span', id=re.compile('SSR_CRSE_OFF_VW_DESCRLONG')).text.strip()
        units = float(soup.find('span', id=re.compile('DERIVED_CRSECAT_UNITS_RANGE')).text.strip())
        grading_basis = soup.find('span', id=re.compile('SSR_CRSE_OFF_VW_GRADING_BASIS')).text.strip()
        academic_level = soup.find('span', id=re.compile('SSR_CRSE_OFF_VW_ACAD_CAREER')).text.strip()
        academic_group = soup.find('span', id=re.compile('ACAD_GROUP_TBL_DESCR')).text.strip()
        academic_org = soup.find('span', id=re.compile('ACAD_ORG_TBL_DESCR')).text.strip()

        # TODO: Generalize into inner function
        course_components: {}

        course_components_rows = soup.find('table', id=re.compile('ACE_SSR_DUMMY_RECVW')).find_all('tr')

        for course_component_row in course_components_rows:
            # first cell is metadata only
            section, required = course_component_row.find_all('td')[1:]
            course_components.update({section: required})

        # TODO: Generalize into inner function
        enroll_info = {}

        # first row is metadata only
        enrollment_info_rows =  soup.find('table', id='ACE_DERIVED_CRSECAT_SSR_GROUP2$0').find_all('tr')[1:]

        for row in enrollment_info_rows:
            enroll_name_raw, enroll_desc_raw = row.find_all('div', id=re.compile('win0divSSR_CRSE_OFF_VW'))
            enroll_name = enroll_name_raw.txet.strip()
            enroll_desc = enroll_desc_raw.text.strip()

            enroll_info.update({ENROLLMENT_INFO_MAP[enroll_name]: enroll_desc})

        # TODO: Generalize into inner function
        ceab_dict = {}

        ceab_units = (soup
            .find('table', id=re.compile('ACE_DERIVED_CLSRCH')) # CEAB table
            .find_all('tr')[1]  # only row with data is 2nd row
            .find_all('td')[1:] # first cell is metadata
            )

        # Iteration by twos. Format: Name, Units
        for i in range(0, len(ceab_units), 2):
            name = ceab_units[i].text.strip().strip(':')
            units = ceab_units[i].text.strip().strip(':')

            ceab_dict.update({name: float(units) if units else 0})

        data = {
            # NOTE: course_id not shown on generic course page. Must do deep
            # scrape of course sections for course_id
            'course_id': None,
            'department': base_info['dept_code'],
            'course_code': base_info['course_code'],
            'course_name': base_info['course_name'],
            'description': description,
            'grading_basis': grading_basis,
            'course_components': course_components,
            'requirements': enroll_info.get('stub', ''),
            'add_consent': enroll_info.get('add_consent', ''),
            'drop_consent': enroll_info.get('drop_consent', ''),
            'academic_level': academic_level,
            'academic_group': academic_group,
            'academic_org': academic_org,
            'units': units,
            'CEAB': ceab_dict,
            }

        return data

