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

            departments = Courses._get_departments(
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

                    params = Courses._remove_params(params, Courses.START_PARAMS.keys())

                    ptus_params = Courses._get_ptus_params(soup)

                    params.update(ic_action)
                    params.update(ptus_params)
                    params.update({'DERIVED_SSTSNAV_SSTS_MAIN_GOTO$27$': '9999'})
                    params.update({'ICBcDomData': 'C~HC_SSS_STUDENT_CENTER~EMPLOYEE~SA~SA_LEARNER_SERVICES.SSS_STUDENT_CENTER.GBL~UnknownValue~Student Center~UnknownValue~UnknownValue~https://saself.ps.queensu.ca/psp/saself/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.SSS_STUDENT_CENTER.GBL~UnknownValue*F~CO_EMPLOYEE_SELF_SERVICE~EMPLOYEE~SA~UnknownValue~UnknownValue~Self Service~UnknownValue~UnknownValue~https://saself.ps.queensu.ca/psp/saself/EMPLOYEE/SA/s/WEBLIB_PT_NAV.ISCRIPT1.FieldFormula.IScript_PT_NAV_INFRAME?pt_fname=CO_EMPLOYEE_SELF_SERVICE&c=SS1fKKYxRTcUmqLHOdRWZg%3d%3d&FolderPath=PORTAL_ROOT_OBJECT.CO_EMPLOYEE_SELF_SERVICE&IsFolder=true~UnknownValue'})

                    import pdb; pdb.set_trace()

                    # TODO: Should be POST (it isn't)
                    soup2 = Scraper.http_request(
                        Courses.host,
                        params=params,
                        cookies=cookies
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


    @staticmethod
    def _get_ptus_params(soup):
        params = {}
        ptus_list = soup.find_all('input', id=re.compile(r'ptus'))

        params.update({
            x.get('name'): x.get('value') for x in ptus_list
            })

        return params


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

        return departments


    # Status: Verified
    @staticmethod
    def _get_courses(department_soup):
        return department_soup.find_all('tr', id=re.compile(r'trCOURSE_LIST'))


    #  TODO: Write it
    @staticmethod
    def parse_course_data(soup):
        pass

