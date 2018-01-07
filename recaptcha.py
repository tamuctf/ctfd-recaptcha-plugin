from flask import request, render_template
from functools import wraps, lru_cache
from .config import config
from lxml import etree
import logging
import requests
import json

#HEAD: <script src="https://www.google.com/recaptcha/api.js" async defer></script>
#FORM:  <div class="g-recaptcha" data-sitekey="your_site_key"></div>

logging.basicConfig(level=logging.DEBUG)

def load(app):
    config(app)

    @lru_cache(maxsize=8)
    def insert_tags(page):
        if isinstance(page, etree._ElementTree):
            root = page
        elif isinstance(page, str) or isinstance(page, bytes):
            root = etree.fromstring(page, etree.HTMLParser())
        else:
            try:
                root = etree.parse(page, etree.HTMLParser())
            except Exception as e:
                raise ValueError("Given page of type '{0}' is not parsable be lxml.etree".format(type(page))) from e

        # Iterate through all forms, but in reality there will only be one
        for form in root.iter('form'):
            form.append(etree.Element('div',
                attrib = {
                    'class': 'g-recaptcha',
                    'data-sitekey': app.config['RECAPTCHA_SECRET']
                }
            ))

        for head in root.iter('head'):
            head.append(etree.Element('script',
                attrib = {
                    'src': 'https://www.google.com/recaptcha/api.js',
                    'async': 'true',
                    'defer': 'true'
                }
            ))


        return etree.tostring(root, method='html')

    def insert_tags_decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            return insert_tags(view_func(*args, **kwargs))

        return wrapper

    def register_decorator(register_func):
        @wraps(register_func)
        def wrapper(*args, **kwargs):
            if request.method == 'POST':
                errors = []
                bad_request = False
                if 'g-recaptcha-response' in request.form and request.form['g-recaptcha-response']:
                    params = {
                        'secret': app.config['RECAPTCHA_SECRET'],
                        'response': request.form['g-recaptcha-response'],
                        'remoteip':  request.remote_addr
                    }
                    request_url = app.config['RECAPTCHA_VERIFY_URL'].format(**params)
                    verify_reponse = requests.post(request_url)
                    logging.debug("Sending reCaptcha verification request: {}".format(request_url))

                    if verify_reponse.ok:
                        verify =  json.loads(verify_reponse.text)
                        logging.debug("Got reCaptcha response: {}".format(verify))
                        if 'error-codes' in verify and verify['error-codes']:
                            bad_request = True
                            logging.error("Google reCaptcha returned error codes {:s}".format(verify['error-codes']))
                        elif verify['success']:
                            logging.debug("{} is human".format(request.form['name']))
                            return register_func(*args, **kwargs)
                    else:
                        bad_request = True
                        logging.error("Google reCaptcha request failed with code {}".format(verify_response.status_code))

                if bad_request:
                    errors.append("Google reCaptcha is currently unavailable. Please try again later")
                else:
                    errors.append("Please check the reCaptcha box to verify you are human")

                return render_template(
                    'register.html',
                    errors=errors,
                    name=request.form['name'],
                    email=request.form['email'],
                    password=request.form['password']
                )
            else:
                return register_func(*args, **kwargs)

        return wrapper

    app.view_functions['auth.register'] = register_decorator(app.view_functions['auth.register'])

    if app.config['RECAPTCHA_INSERT_TAGS']:
        app.view_functions['auth.register'] = insert_tags_decorator(app.view_functions['auth.register'])
