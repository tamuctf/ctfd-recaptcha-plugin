from flask import request, render_template
from functools import wraps
from .config import config
from lxml import etree
import logging
import requests
import json

#HEAD: <script src="https://www.google.com/recaptcha/api.js" async defer></script>
#FORM:  <div class="g-recaptcha" data-sitekey="your_site_key"></div>

logging.basicConfig(level=logging.DEBUG)

def singleton_cache(func):
    """Stores a single return value and reevaluates if the args change"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        null = object() # A special value because None is a valid return
        cache = null
        cache_args = null

        if cache is null or cache_args != (args, kwargs):
            try:
                cache = func(*args, **kwargs)
                cache_args = (args, kwargs)

            # On failure unset the cache
            except:
                cache = null
                cache_args = null
                raise

        return cache
    return wrapper

def load(app):
    config(app)

    @singleton_cache
    def insert_tags(page):
        if isinstance(page, etree._ElementTree):
            root = page
        else:
            root = etree.fromstring(page, etree.HTMLParser())

        # Insert the check box to the left of the submit button
        # Iterate through all forms adn buttons, but in reality there will only be one
        # unless the developer is doing a non-trivial custom theme
        # in which case they will turn off the automatic insert feature
        for form in root.iter('form'):
            for child in form.iterchildren():
                for button in child.xpath('.//button[@type="submit"]'):
                    button.addprevious(
                        etree.Element('div',
                            attrib = {
                                'class': 'g-recaptcha float-left',
                                'data-sitekey': app.config['RECAPTCHA_SECRET']
                            }
                        )
                    )

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
