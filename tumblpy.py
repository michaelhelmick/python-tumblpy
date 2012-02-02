#!/usr/bin/env python

""" Tumblpy """

__author__ = 'Mike Helmick <mikehelmick@me.com>'
__version__ = '0.2.0'

import urllib
import time

try:
    from urlparse import parse_qsl
except ImportError:
    from cgi import parse_qsl

import oauth2 as oauth
import httplib2

try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        try:
            from django.utils import simplejson as json
        except ImportError:
            raise ImportError('A json library is required to use this python library. Lol, yay for being verbose. ;)')


class TumblpyError(Exception):
    """ Generic error class, catch-all for most Tumblpy issues.

        from Tumblpy import TumblpyError, TumblpyRateLimitError, TumblpyAuthError
    """
    def __init__(self, msg, error_code=None):
        self.msg = msg
        if error_code == 503:
            raise TumblpyRateLimitError(msg)
        elif error_code == 401:
            raise TumblpyAuthError(msg)

    def __str__(self):
        return repr(self.msg)


class TumblpyRateLimitError(TumblpyError):
    """
        Raised when you've hit an API limit. Try to avoid these, read the API
        docs if you're running into issues here, Tumblthon does not concern itself with
        this matter beyond telling you that you've done goofed.
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class TumblpyAuthError(TumblpyError):
    """ Raised when you try to access a protected resource and it fails due to some issue with your authentication. """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class Tumblpy(object):
    def __init__(self, app_key=None, app_secret=None, oauth_token=None, oauth_token_secret=None, headers=None, client_args=None):
        # Define some API URLs real quick
        self.base_api_url = 'http://api.tumblr.com'
        self.api_version = 'v2'
        self.api_url = '%s/%s/' % (self.base_api_url, self.api_version)

        # Authentication URLs
        self.request_token_url = 'http://www.tumblr.com/oauth/request_token'
        self.access_token_url = 'http://www.tumblr.com/oauth/access_token'
        self.authorize_url = 'http://www.tumblr.com/oauth/authorize'
        self.authenticate_url = 'http://www.tumblr.com/oauth/authorize'

        self.app_key = app_key
        self.app_secret = app_secret
        self.oauth_token = oauth_token
        self.oauth_secret = oauth_token_secret

        self.default_params = {'api_key': self.app_key}

        # If there's headers, set them. If not, lets
        self.headers = headers or {'User-agent': 'Tumblpy %s' % __version__}

        self.consumer = None
        self.token = None

        client_args = client_args or {}

        # See if they're authenticating for the first or if they already have some tokens.
        # http://michaelhelmick.com/tokens.jpg
        if self.app_key is not None and self.app_secret is not None:
            self.consumer = oauth.Consumer(key=self.app_key, secret=self.app_secret)

        if self.oauth_token is not None and self.oauth_secret is not None:
            self.token = oauth.Token(key=oauth_token, secret=oauth_token_secret)

        if self.consumer is not None and self.token is not None:
            # Authenticated
            self.client = oauth.Client(self.consumer, self.token, **client_args)
        elif self.consumer is not None:
            # Authenticating
            self.client = oauth.Client(self.consumer, **client_args)
        else:
            # Unauthenticated requests (in case Tumblr decides to open up some API calls to public)
            self.client = httplib2.Http(**client_args)

    def get_authentication_tokens(self):
        """ So, you want to get an authentication url?

            t = Tumblpy(YOUR_CONFIG)
            auth_props = t.get_authentication_tokens()
            auth_url = auth_props['auth_url']
            print auth_url
        """
        resp, content = self.client.request(self.request_token_url, 'GET')

        status = int(resp['status'])
        if status != 200:
            raise TumblpyAuthError('There was a problem authenticating you. Error: %s, Message: %s' % (status, content))

        request_tokens = dict(parse_qsl(content))

        auth_url_params = {
            'oauth_token': request_tokens['oauth_token'],
        }

        request_tokens['auth_url'] = self.authenticate_url + '?' + urllib.urlencode(auth_url_params)

        return request_tokens

    def get_access_token(self, oauth_verifier):
        """ After being returned from the callback, call this.

            t = Tumblpy(YOUR_CONFIG)
            authorized_tokens = t.get_access_token(oauth_verifier)
            oauth_token = authorized_tokens['oauth_token']
            oauth_token_secret = authorized_tokens['oauth_token_secret']
        """
        resp, content = self.client.request('%s?oauth_verifier=%s' % (self.access_token_url, oauth_verifier), 'GET')
        return dict(parse_qsl(content))

    def api_request(self, endpoint, blog_url=None, method='GET', extra_endpoints=None, params=None):
        params = params or {}

        # http://api.tumblr.com/v2/
        url = self.api_url

        if blog_url is not None:
            # http://api.tumblr.com/v2/blog/blogname.tumblr.com/
            blog_url = blog_url.rstrip('/')
            if blog_url.startswith('http://'):
                blog_url = blog_url[7:]

            url = '%sblog/%s/' % (self.api_url, blog_url)

        url = '%s%s/' % (url, endpoint)
        if extra_endpoints is not None:
            # In cases like:
            # http://api.tumblr.com/v2/blog/blogname.tumblr.com/posts/type/
            # 'type' is extra in the url and this was the best way I thought to do this.
            # Docs: http://www.tumblr.com/docs/en/api/v2#posts

            url = '%s/%s' % (url, '/'.join(extra_endpoints))

        params.update(self.default_params)

        self.headers.update({'Content-Type': 'application/json'})

        if method == 'POST':
            params = {
                'oauth_version': "1.0",
                'oauth_nonce': oauth.generate_nonce(),
                'oauth_timestamp': int(time.time()),
                'oauth_token': self.token.key,
                'oauth_consumer_key': self.consumer.key,
            }

            req = oauth.Request(method='POST', url=url, parameters=params)

            ## Sign the request.
            signature_method = oauth.SignatureMethod_HMAC_SHA1()
            req.sign_request(signature_method, self.consumer, self.token)

            resp, content = self.client.request(req.to_url(), 'POST', headers=self.headers)
        else:
            url = '%s?%s' % (url, urllib.urlencode(params))
            resp, content = self.client.request(url, 'GET', headers=self.headers)

        status = int(resp['status'])  # I don't know why Tumblr doesn't return status as an it, but let's cast it to an int..
        if status < 200 or status >= 300:
            raise TumblpyError('There was an error making your request.', error_code=status)

        content = json.loads(content)

        return content['response']

    def post(self, endpoint, blog_url=None, extra_endpoints=None, params=None):
        params = params or {}
        return self.api_request(endpoint, method='POST', blog_url=blog_url, extra_endpoints=extra_endpoints, params=params)

    def get(self, endpoint, blog_url=None, extra_endpoints=None, params=None):
        params = params or {}
        return self.api_request(endpoint, method='GET', blog_url=blog_url, extra_endpoints=extra_endpoints, params=params)
