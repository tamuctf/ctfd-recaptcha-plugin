from os import environ
from enum import Enum

def envvar(key, default=None):
    '''Return a variable from the environment, or the default. Includes a check for deprecated RECAPTCHA_* keys for back compat.'''
    value = environ.get(key, None)
    if value is not None:
        return value

    if key.startswith('CAPTCHA'):
        return environ.get('RE' + key, default)

    return default

def config(app):
    '''
    CAPTCHA_PROVIDER configures which captcha provider to use. Options are reCaptcha and hCaptcha.
    '''
    app.config['CAPTCHA_PROVIDER'] = environ.get('CAPTCHA_PROVIDER', None)

    '''
    CAPTCHA_ENABLED determines whether or not to use the recaptcha feature. Set to False for debugging or otherwise turning off recaptcha.
    '''
    app.config['CAPTCHA_ENABLED'] = envvar('CAPTCHA_ENABLED', "True").lower() == 'true'

    '''
    CAPTCHA_SECRET is the secret key provided to you by Google for reCaptcha
    You may either set the CAPTCHA_SECRET env variable or save it here in this file
    '''
    app.config['CAPTCHA_SECRET'] = envvar('CAPTCHA_SECRET', 'INVALID_SECRET')

    '''
    CAPTCHA_SITE_KEY is the public site key provided to you by Google for reCaptcha
    Needed if `CAPTCHA_INSERT_TAGS` is True
    You may either set the CAPTCHA_SITE_KEY env variable or save it here in this file
    '''
    app.config['CAPTCHA_SITE_KEY'] = envvar('CAPTCHA_SITE_KEY', 'INVALID_SITE_KEY')

    '''
    CAPTCHA_INSERT_TAGS determines if the plugin should automatically attempt to insert tags (i.e. the script and check box)
    This works well if the registration template is not heavily modified, but set this to false if you want to control where the
    check box appears
    '''
    app.config['CAPTCHA_INSERT_TAGS'] = envvar('CAPTCHA_INSERT_TAGS', 'True').lower() == 'true'

    '''
    CAPTCHA_VERIFY_REMOTE_IP should be True if you want to include the client ip address in the verification step.
    '''
    app.config['CAPTCHA_VERIFY_REMOTE_IP'] = envvar('CAPTCHA_VERIFY_REMOTE_IP', 'False').lower() == 'true'
