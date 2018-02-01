import time
import json
import requests
import chromedriver_binary # Adds chromedriver_binary to path

from bs4 import BeautifulSoup
from selenium import webdriver
from pymongo import MongoClient
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp, */*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch, br',
    'Accept-Language': 'en-US,en;q=0.8',
    'Cache-Control': 'no-cache',
    'dnt': '1',
    'Pragma': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
}

def requests_sample():
    res = requests.get('https://news.ycombinator.com')
    soup = BeautifulSoup(res.text, 'html.parser')

    rows = soup.find_all('tr', 'athing')

    info = []

    for row in rows:
        title = row.find('a', 'storylink').text.strip()
        link = row.find('a', 'storylink')['href']

        data = {
            'title': title,
            'link': link,
        }

        print(json.dumps(data, indent=2))

    print('\nDONE')

def write_sample():
    results = []

    for i in range(5):
        num = i + 1

        data = {
            'age': str(num),
            'name': 'Johnny '.join(str(num)),
            'team': 'Team '.join(str(num)),
        }

        results.append(data)

    results_json = json.dumps(
                        results,
                        indent=2,
                        sort_keys=True,
                        ensure_ascii=False,
                        )

    for result in results:
        result_json = json.dumps(
                        result,
                        indent=2,
                        sort_keys=True,
                        ensure_ascii=False,
                        )

        with open('sample.json', 'a+') as f:
            f.write(result_json)

    print('\nDONE')


def write_to_mongodb_sample():
    client = MongoClient('localhost', 27017)
    db = client['myNewDatabase']
    collection = db['myCollection']

    post = {
        'author': 'Alex',
        'text': 'THE GENESIS OF KNOWLEDGE',
        'tags': ['mongodb', 'python', 'pymongo'],
    }

    collection.insert_one(post)

    print('\nDONE')


def retry_sample():
    t0 = time.time()
    try:
        response = requests_retry_session().get(
            'http://localhost:9999',
        )
    except Exception as x:
        print('It failed :(', x.__class__.__name__)
        print('More Details:', x)
    else:
        print('It eventually worked', response.status_code)
    finally:
        t1 = time.time()
        print('Took', t1 - t0, 'seconds')


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None
):
    session = session or requests.Session()
    session.headers.update(headers)
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session


def login_to_solus_sample():
    import pdb; pdb.set_trace()
    login_url = "https://my.queensu.ca"
    continue_url = "SAML2/Redirect/SSO"

    session = requests_retry_session()
    res = session.get(login_url)
    payload = {
       'j_username': '12aa100',
       'j_password': 'Radix124c41+',
       'IDButton': '%C2%A0Log+In%C2%A0',
        }

    res = session.post(res.url, data=payload)

        # Check for the continue page
    if continue_url in res.url:
        res = do_continue_page(res, session)

    # Should now be authenticated and on the my.queensu.ca page, submit a
    # request for the URL in the 'SOLUS' button
    link = login_solus_link(res)
    if not link:
        # Not on the right page
        raise EnvironmentError("Could not authenticate with the Queen's SSO system. The login credentials provided may have been incorrect.")

    print("Sucessfully authenticated.")
    # Have to actually use this link to access SOLUS initially otherwise it asks for login again
    res = requests_retry_session().get(link)

    # The request could (seems 50/50 from browser tests) bring up another
    # continue page
    if continue_url in latest_response.url:
        res = do_continue_page(res, session)

    print("Sucessfully authenticated x2.")

    # Should now be logged in and on the student center page

def do_continue_page(res, session):
    import pdb; pdb.set_trace()
    """
    The SSO system returns a specific page only if JS is disabled. It has you
    click a Continue button which submits a form with some hidden values
    """
    redirect_url = "https://login.queensu.ca"
    data = login_continue_page(res)

    if not data:
        return

    url = urljoin(redirect_url, data['url'])

    return session.post(url, data=data["payload"])

def login_continue_page(res):
    import pdb; pdb.set_trace()
    """Return the url and payload to post from the continue page"""

    #Grab the RelayState, SAMLResponse, and POST url
    soup = BeautifulSoup(res.text, 'html.parser')
    form = soup.find("form")

    if not form:
        # No form, nothing to be done
        return None

    url = form.get("action")

    payload = {}

    for x in form.find_all("input", type="hidden"):
        payload[x.get("name")] = x.get("value")

    return dict(url=url, payload=payload)

def login_solus_link(res):
    import pdb; pdb.set_trace()
    """Return the href of the SOLUS link"""

    soup = BeautifulSoup(res.text, 'html.parser')
    link = soup.find("a", text="SOLUS")

    if link:
        return link.get("href")

# =============== HEADLESS WEB DRIVER APPROACH FOR SOLUS LOGIN  ===============

def solus_login():
    chrome_options = Options()
    chrome_options.add_argument('--headless')

    driver = webdriver.Chrome()

    driver.get('https://my.queensu.ca')
    # TODO: To Be Continued

if __name__ == '__main__':
    solus_login()
