'''
VERIFY_REMOTE_IP should be True if you want to include the client ip address in the verification step. 
'''
VERIFY_REMOTE_IP = False

def config(app):
    '''
    RECAPTCHA_SECRET is the secret key provided to you by Google for reCaptcha
    '''
    app.config['RECAPTCHA_SECRET'] = 'YOUR_SECRET_HERE'

    
    if VERIFY_REMOTE_IP:
        app.config['RECAPTCHA_VERIFY_URL'] = 'https://www.google.com/recaptcha/api/siteverify?secret={secret:s}&response={response:s}&remoteip={remoteip:s}'
    else:
        app.config['RECAPTCHA_VERIFY_URL'] = 'https://www.google.com/recaptcha/api/siteverify?secret={secret:s}&response={response:s}'
