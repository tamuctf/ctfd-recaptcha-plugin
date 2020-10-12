# CTFd Captcha Plugin

A plugin which adds the [Google reCaptcha v2](https://developers.google.com/recaptcha/docs/display) or [hCaptcha](https://www.hcaptcha.com/) checkbox to the registration page to prevent automated created of accounts on your CTF.

> Note: Although Google reCaptcha has a longer track record of security, I personally recommend using hCaptcha for it's commitment to user privacy.

### Setup

1. Create an account with your captcha provider and add your site.
  * [Google reCaptcha](https://www.google.com/recaptcha/admin): Create a v2 checkbox site and obtain the site key and sceret
  * [hCaptcha](https://dashboard.hcaptcha.com/): Create a new site and obtain it's site key. Obtain the secret for your account.
2. Clone this repo into a folder in the plugin folder of your CTFd
3. Set the configuration variables either as environment variables or by editing `config.py` in this repo.
  * Set `CAPTCHA_PROVIDER` to `reCaptcha` or `hCaptcha` depending on your preferences.
  * Set `CAPTCHA_SECRET` and `CAPTCHA_SITE_KEY` your captcha keys.

### Options

Additional options, configurable either through environment variable or by editing `config.py` in this repo.

* `CAPTCHA_ENABLED` (default: True): Determines whether or not to use the recaptcha feature. Set to False for debugging or otherwise turning off recaptcha.
* `CAPTCHA_PROVIDER` (required): Configures which captcha provider to use. Options are reCaptcha and hCaptcha.
* `CAPTCHA_SECRET` (required): The secret key provided to you by Google for reCaptcha.
* `CAPTCHA_SITE_KEY` (required): The public site key provided to you by Google for reCaptcha.
* `CAPTCHA_INSERT_TAGS` (default: True): Determines if the plugin should automatically attempt to insert tags (i.e. the script and check box). This works well if the registration template is not heavily modified, but set this to false if you want to control where the check box appears.
* `CAPTCHA_VERIFY_REMOTE_IP` (default: False): Should be `True` if you want to include the client ip address in the verification step.
