from flask import request, render_template
from functools import wraps
from config import config
import logging
import requests
import json


#logging.basicConfig(level=logging.DEBUG)

def load(app):
    config(app)

    def register_decorator(register_func):
        @wraps(register_func)
        def wrapper():
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
                    #logging.debug("Sending reCaptcha verification request: {}".format(request_url))

                    if verify_reponse.ok:
                        verify =  json.loads(verify_reponse.text)
                        #logging.debug("Got reCaptcha response: {}".format(verify))
                        if 'error-codes' in verify and verify['error-codes']:
                            bad_request = True
                            logging.error("Google reCaptcha returned error codes {:s}".format(verify['error-codes']))
                        elif verify['success']:
                            #logging.debug("{} is human".format(request.form['name']))
                            return register_func()
                    else:
                        bad_request = True
                        logging.error("Google reCaptcha request failed with code {}".format(verify_response.status_code))

                if bad_request:
                    errors.append("Google reCaptcha is currently unavailable. Please try again later")
                else:
                    errors.append("Please check the reCaptcha box to verify you are human")

                return render_template('register.html', errors=errors, name=request.form['name'], email=request.form['email'], password=request.form['password'])
            else:
                return register_func()
            
        return wrapper

    app.view_functions['auth.register'] = register_decorator(app.view_functions['auth.register'])
