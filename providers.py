from abc import ABC, abstractmethod
from lxml import etree
from requests.exceptions import RequestException
from urllib.parse import urlencode
import logging
import requests

logger = logging.getLogger('captcha')

class VerificationError(Exception):
    '''Raised when verification could not be completed, such as when the provider returns an error.'''

class CaptchaProvider(ABC):
    @property
    @abstractmethod
    def verification_url(self):
        pass

    @property
    @abstractmethod
    def response_form_key(self):
        pass

    @classmethod
    def parse(cls, string):
        if string is None:
            raise ValueError('Captcha provider unspecified. Options include "Google" and "hCpatcha"')

        if string.lower() in ['google', 'recaptcha', 're']:
            return ReCaptchaProvider
        if string.lower() in ['intuition machines', 'hcaptcha', 'h']:
            return HCaptchaProvider

        raise ValueError('{!r} could not be parsed as a captcha provider')

    @abstractmethod
    def script_tag(self):
        pass

    @abstractmethod
    def challenge_tag(self):
        pass

    def post_data(self, response, remote_ip=None):
        data = {
            'secret': self.secret,
            'response': response,
        }

        if self.verify_remote_ip:
            if remote_ip is None:
                logger.error("Configured to verify remote IP, but remote IP was not provided.")
                raise VerificationError()
            data['remoteip'] = remote_ip

        return data

    def verify(self, form, remote_ip=None):
        # If the form did not include a captcha response, fail immediately.
        if not form.get(self.response_form_key, None):
            return False

        # Make the request to the captcha provider.
        post_data = self.post_data(form[self.response_form_key], remote_ip)
        logger.debug("Sending captcha verification request {} to {}".format(post_data, self.verification_url))
        verify_reponse = requests.post(self.verification_url, data=post_data)

        # If the HTTP request failed, bail.
        try:
            verify_reponse.raise_for_status()
        except RequestException as e:
            logger.error("Captcha request failed with code {}".format(verify_response.status_code))
            raise VerificationError() from e

        # Parse the response and check for error codes.
        verify = verify_reponse.json()
        logger.debug("Got captcha verification response: {}".format(verify))
        if verify.get('error-codes', None):
            logger.error("Captcha service returned error codes {}".format(verify['error-codes']))
            raise VerificationError()

        return verify['success']

class ReCaptchaProvider(CaptchaProvider):
    verification_url = 'https://www.google.com/recaptcha/api/siteverify'
    response_form_key = 'g-recaptcha-response'

    def __init__(self, site_key, secret, verify_remote_ip=False):
        self.site_key = site_key
        self.secret = secret
        self.verify_remote_ip = verify_remote_ip

    def script_tag(self):
        return etree.Element(
            'script',
            attrib = {
                'src': 'https://www.google.com/recaptcha/api.js',
                'async': 'true',
                'defer': 'true'
            }
        )

    def challenge_tag(self):
        return etree.Element(
            'div',
            attrib = {
                'class': 'g-recaptcha float-left',
                'data-sitekey': self.site_key,
            }
        )

class HCaptchaProvider(CaptchaProvider):
    verification_url = 'https://hcaptcha.com/siteverify'
    response_form_key = 'h-captcha-response'

    def __init__(self, site_key, secret, verify_remote_ip=False):
        self.site_key = site_key
        self.secret = secret
        self.verify_remote_ip = verify_remote_ip

    def script_tag(self):
        return etree.Element(
            'script',
            attrib = {
                'src': 'https://hcaptcha.com/1/api.js',
                'async': 'true',
                'defer': 'true'
            }
        )

    def challenge_tag(self):
        return etree.Element(
            'div',
            attrib = {
                'class': 'h-captcha float-left',
                'data-sitekey': self.site_key,
            }
        )

    def post_data(self, response, remote_ip=None):
        data = {
            'secret': self.secret,
            'sitekey': self.site_key,
            'response': response,
        }

        if self.verify_remote_ip:
            if remote_ip is None:
                logger.error("Configured to verify remote IP, but remote IP was not provided.")
                raise VerificationError()
            data['remoteip'] = remote_ip

        return data
