# ==== PERSONAL STEPS TO AUTHENTICATING ON SOLUS ====

s = requests.session()
login_url = 'https://my.queensu.ca'
continue_url = "SAML2/Redirect/SSO"
course_catalog_url = "https://saself.ps.queensu.ca/psc/saself/EMPLOYEE/HRMS/c/SA_LEARNER_SERVICES.SSS_BROWSE_CATLG_P.GBL"
payload = {
    'j_username': <NetID>,
    'j_password': <password>,
    'IDButton': 'Log In',
}

res = s.post(login_url, data=payload)

# res.url will be something like:
# https://login.queensu.ca/idp/profile/SAML2/Redirect/SSO;jsessionid=372E3242251C90214B61F79865B8B9DD?execution=e1s1

# we must be redirected, grab Shibboleth info from there and redirect
if continue_url in res.url:
    soup = BeautifulSoup(res.text, 'html.parser')

    #Grab the RelayState, SAMLResponse, and POST url
    form = soup.find('form')

    # if no form, nothing to do here
    if not form:
        return

    # url will be something like: '/idp/profile/SAML2/Redirect/SSO?execution=e3s1'
    url = form.get('action')
    payload = {}

    inputs = form.find_all('input', type='hidden')

    for input in inputs:
        key = input.get('name')
        value = input.get('value')

        payload[key] = value

    info = dict(url=url, payload=payload)

new_url = urljoin(login_url, data['url'])

res = s.post(new_url, data=data['payload'])
