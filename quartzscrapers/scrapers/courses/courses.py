import re
import chromedriver_binary # Adds chromedriver_binary to path

from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from ..utils import Scraper
from ..utils.config import QUEENS_USERNAME, QUEENS_PASSWORD
from .courses_helpers import noop


class Courses:
    '''
    A scraper for Queen's courses.

    <Lorem Ipsum insert some explanatory text here>
    '''

    host = 'https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/HRMS/c/SA_LEARNER_SERVICES.CLASS_SEARCH.GBL'
    headers = {
        'Pragma': 'no-cache',
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Accept-Language': 'en-US,en;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/HRMS/c/SA_LEARNER_SERVICES.SSS_STUDENT_CENTER.GBL?PortalActualURL=https%3a%2f%2fsaself.ps.queensu.ca%2fpsc%2fsaself%2fEMPLOYEE%2fHRMS%2fc%2fSA_LEARNER_SERVICES.SSS_STUDENT_CENTER.GBL&PortalContentURL=https%3a%2f%2fsaself.ps.queensu.ca%2fpsc%2fsaself%2fEMPLOYEE%2fHRMS%2fc%2fSA_LEARNER_SERVICES.SSS_STUDENT_CENTER.GBL&PortalContentProvider=HRMS&PortalCRefLabel=Student%20Center&PortalRegistryName=EMPLOYEE&PortalServletURI=https%3a%2f%2fsaself.ps.queensu.ca%2fpsp%2fsaself%2f&PortalURI=https%3a%2f%2fsaself.ps.queensu.ca%2fpsc%2fsaself%2f&PortalHostNode=HRMS&NoCrumbs=yes&PortalKeyStruct=yes',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        }

    IC_ACTIONS = {
        'adv_search': 'DERIVED_CLSRCH_SSR_EXPAND_COLLAPS$149$$1',
        }

    @staticmethod
    def scrape():
        '''Update database records for courses scraper'''

        params = {
            'Page': 'SSR_CLSRCH_ENTRY',
            'Action': 'U',
            'ExactKeys': 'Y',
            'TargetFrameName': 'None'
            }

        session_cookies = Courses.login()

        # Note: May not be necessary
        # hidden_params = Courses._get_hidden_params(soup)
        # hidden_params.update(Courses.IC_ACTIONS['adv_search'])

        params.update(Courses.IC_ACTIONS['adv_search'])

        # TODO: Build in post requests into base scraper request function
        soup = Scraper.http_request(Courses.host, params=params, cookies=cookies)

        initially_selected_term = Courses._get_selected_term(soup)
        advanced_search_params = Courses._get_advanced_search_params(soup)

        params.update(advanced_search_params)

        departments = Courses._get_departments(soup)


    @staticmethod
    def login():
        chrome_options = Options()
        chrome_options.add_argument('--headless')

        driver = webdriver.Chrome()
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(30)
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

        # TODO: Consider
        session_cookies = {}

        for cookie in driver.get_cookies():
            session_cookies[cookie['name']] = cookie['value']

        driver.close()

        return session_cookies


    # Note: May not be necessary
    @staticmethod
    def _get_hidden_params(soup):
        params = {}

        hidden = soup.find('div', id=re.compile(r'win\ddivPSHIDDENFIELDS'))

        if not hidden:
            hidden = soup.find('field', id=re.compile(r'win\ddivPSHIDDENFIELDS'))

        params.update({
            x.get('name'): x.get('value') for x in hidden.find_all('input')
            })

        return params


    @staticmethod
    def _get_selected_term(soup):
        selected_term =
            (soup.find('select', id='CLASS_SRCH_WRK2_STRM$35$')
                .find('option', selected='selected'))

        return selected_term


    @staticmethod
    def _get_advanced_search_params(soup):
        refined_search_query = {
        'SSR_CLSRCH_WRK_SSR_OPEN_ONLY$chk$5': 'N',
        'SSR_CLSRCH_WRK_INCLUDE_CLASS_DAYS$8': 'J',
        }

        for day in ['MON', 'TUES', 'WED', 'THURS', 'FRI', 'SAT', 'SUN']:
            refined_search_query.update({
                'SSR_CLSRCH_WRK_{day}$chk$8'.format(day=day): 'Y',
                'SSR_CLSRCH_WRK_{day}$8'.format(day=day): 'Y',
                })

        return refined_search_query


    @staticmethod
    def _get_dept_param_key(soup):
        return soup.find(
            'select',
            id=re.compile(r'SSR_CLSRCH_WRK_SUBJECT_SRCH\$\d')
            )['id']


    @staticmethod
    def _get_departments(soup):
        dept_soups = soup.find(
            'select',
            id=re.compile(r'SSR_CLSRCH_WRK_SUBJECT_SRCH\$\d')
            ).find_all('option')[1:]

        departments = {
            dept['value']: dept.text for dept in dept_soups
            }

        return departments


    @staticmethod
    def foo(bar):
        pass


    @staticmethod
    def foo(bar):
        pass


    @staticmethod
    def foo(bar):
        pass

    @staticmethod
    def foo(bar):
        pass