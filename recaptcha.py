from .config import config
from flask import request, render_template
from functools import wraps
from lxml import etree
import json
import logging
import os
import requests

logger = logging.getLogger('naumachia')

def load(app):
    config(app)

    if not app.config['RECAPTCHA_ENABLED']:
        return

    # Intitialize logging.
    logger.setLevel(app.config.get('LOG_LEVEL', "INFO"))

    log_dir = app.config.get('LOG_FOLDER', os.path.join(os.path.dirname(__file__), 'logs'))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'captcha.log')

    if not os.path.exists(log_file):
        open(log_file, 'a').close()

    handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=10000)
    logger.addHandler(handler)
    logger.propagate = 0

    def insert_tags(page):
        if isinstance(page, etree._ElementTree):
            root = page
        else:
            try:
                root = etree.fromstring(page, etree.HTMLParser())
            except:
                # We couldn't parse it (e.g. it is a Response object) so just pass it through
                return page

        # Insert the check box to the left of the submit button
        # Iterate through all forms adn buttons, but in reality there will only be one
        # unless the developer is doing a non-trivial custom theme
        # in which case they will turn off the automatic insert feature
        inserted_div, inserted_script = False, False
        for form in root.iter('form'):
            for button in form.xpath('.//button[@type="submit"] | .//input[@type="submit"]'):
                button.addprevious(
                    etree.Element('div',
                        attrib = {
                            'class': 'g-recaptcha float-left',
                            'data-sitekey': app.config['RECAPTCHA_SITE_KEY']
                        }
                    )
                )
                logger.debug("Inserted captcha checkbox element into page")
                inserted_div = True

        for head in root.iter('head'):
            head.append(etree.Element('script',
                attrib = {
                    'src': 'https://www.google.com/recaptcha/api.js',
                    'async': 'true',
                    'defer': 'true'
                }
            ))
            logger.debug("Inserted captcha script tag into page head")
            inserted_script = True

        if not inserted_div and inserted_script:
            logger.error('Failed to insert capctha elements into page: inserted_div={!s}, inserted_script={!s}'.format(inserted_div, inserted_script))

        return etree.tostring(root, method='html')

    try:
        from functools import lru_cache
        insert_tags = lru_cache(maxsize=8)(insert_tags)
    except ImportError:
        pass

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
                    logger.debug("Sending reCaptcha verification request: {}".format(request_url))

                    if verify_reponse.ok:
                        verify =  json.loads(verify_reponse.text)
                        logger.debug("Got reCaptcha response: {}".format(verify))
                        if 'error-codes' in verify and verify['error-codes']:
                            bad_request = True
                            logger.error("Google reCaptcha returned error codes {}".format(verify['error-codes']))
                        elif verify['success']:
                            logger.debug("{} is human".format(request.form['name']))
                            return register_func(*args, **kwargs)
                    else:
                        bad_request = True
                        logger.error("Google reCaptcha request failed with code {}".format(verify_response.status_code))

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
