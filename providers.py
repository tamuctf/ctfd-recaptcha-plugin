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
    @classmethod
    def parse(cls, string):
        if string is None:
            raise ValueError('Captcha provider unspecified. Options include "Google" and "hCpatcha"')

        if string.lower() in ['google', 'recaptcha', 're']:
            return ReCaptchaProvider
        if string.lower() in ['intuition machines', 'hcaptcha', 'h']:
            raise NotImplementedError('hCatcha support is not yet implemented')

        raise ValueError('{!r} could not be parsed as a captcha provider')

    @abstractmethod
    def script_tag(self):
        pass

    @abstractmethod
    def challenge_tag(self):
        pass

    @abstractmethod
    def verify(self, form):
        pass

class ReCaptchaProvider(CaptchaProvider):
    def __init__(self, secret, verify_remote_ip=False):
        self.secret = secret
        self.verify_remote_ip = verify_remote_ip

    def script_tag(self):
        raise NotImplementedError()

    def challenge_tag(self):
        raise NotImplementedError()

    def verification_url(self, secret, response, remote_ip):
        base = 'https://www.google.com/recaptcha/api/siteverify'
        if self.verify_remote_ip:
            params = {
                'secret': secret,
                'response': response,
                'remoteip': remote_ip,
            }
        else:
            params = {
                'secret': secret,
                'response': response,
            }
        return '{:s}?{:s}'.format(base, urlencode(params))

    def verify(self, form, remote_ip=None):
        # If the form did not include a captcha response, fail immediately.
        if not form.get('g-recaptcha-response', None):
            return False

        # Construct and send a request to the captcha service.
        request_url = self.verification_url(
            secret = self.secret,
            response = form['g-recaptcha-response'],
            remote_ip = remote_ip
        )
        logger.debug("Sending reCaptcha verification request: {}".format(request_url))
        verify_reponse = requests.post(request_url)

        # If the HTTP request failed, bail.
        try:
            verify_reponse.raise_for_status()
        except RequestException as e:
            logger.error("Google reCaptcha request failed with code {}".format(verify_response.status_code))
            raise VerificationError() from e

        # Parse the response and check for error codes.
        verify = verify_reponse.json()
        logger.debug("Got reCaptcha response: {}".format(verify))
        if verify.get('error-codes', None):
            logger.error("Google reCaptcha returned error codes {}".format(verify['error-codes']))
            raise VerificationError()

        return verify['success']
