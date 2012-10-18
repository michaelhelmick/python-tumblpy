""" Tumblpy """

__author__ = 'Mike Helmick <mikehelmick@me.com>'
__version__ = '0.6.3'

import requests
from requests.auth import OAuth1

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

try:
    from urlparse import parse_qsl
except ImportError:
    from cgi import parse_qsl

import urllib


def _split_params_and_files(params_):
        params = {}
        files = {}
        for k, v in params_.items():
            if hasattr(v, 'read') and callable(v.read):
                files[k] = v
            elif isinstance(v, basestring):
                params[k] = v
            elif isinstance(v, bool):
                params[k] = 'true' if v else 'false'
            elif isinstance(v, int):
                params[k] = unicode(v)
            else:
                raise TumblpyError('Value for "%s" was not parsable.' % k)
        return params, files


class TumblpyError(Exception):
    """Generic error class, catch-all for most Tumblpy issues.
    from tumblpy import TumblpyError, TumblpyRateLimitError, TumblpyAuthError
    """
    def __init__(self, msg, error_code=None):
        self.msg = msg
        self.error_code = error_code
        if error_code is not None:
            if error_code == 503:
                raise TumblpyRateLimitError(msg, error_code)
            elif error_code == 401:
                raise TumblpyAuthError(msg, error_code)

    def __str__(self):
        return repr(self.msg)


class TumblpyRateLimitError(TumblpyError):
    """Raised when you've hit an API limit."""
    def __init__(self, msg, error_code=None):
        self.msg = msg
        self.error_code = error_code

    def __str__(self):
        return repr(self.msg)


class TumblpyAuthError(TumblpyError):
    """Raised when you try to access a protected resource and it fails due to
     some issue with your authentication."""
    def __init__(self, msg, error_code=None):
        self.msg = msg
        self.error_code = error_code

    def __str__(self):
        return repr(self.msg)


class Tumblpy(object):
    def __init__(self, app_key=None, app_secret=None, oauth_token=None, \
                oauth_token_secret=None, headers=None, callback_url=None, \
                pool_maxsize=None):

        # Define some API URLs real quick
        self.base_api_url = 'http://api.tumblr.com'
        self.api_version = 'v2'
        self.api_url = '%s/%s/' % (self.base_api_url, self.api_version)

        # Authentication URLs
        self.request_token_url = 'http://www.tumblr.com/oauth/request_token'
        self.access_token_url = 'https://www.tumblr.com/oauth/access_token'
        self.authorize_url = 'https://www.tumblr.com/oauth/authorize'
        self.authenticate_url = 'https://www.tumblr.com/oauth/authorize'

        self.callback_url = callback_url

        self.default_params = {'api_key': app_key}

        # If there's headers, set them, otherwise be an embarassing parent
        self.headers = headers or {'User-Agent': 'Tumblpy v' + __version__}

        if pool_maxsize:
            requests_config = {'pool_maxsize': pool_maxsize}
        else:
            requests_config = {}

        # Allow for unauthenticated requests
        self.client = requests.session(config=requests_config)
        self.auth = None

        if app_key and app_secret:
            self.app_key = unicode(app_key) or app_key
            self.app_secret = unicode(app_secret) or app_key

        if oauth_token and oauth_token_secret:
            self.oauth_token = unicode(oauth_token)
            self.oauth_token_secret = unicode(oauth_token_secret)

        if app_key and app_secret and not oauth_token and not oauth_token_secret:
            self.auth = OAuth1(self.app_key, self.app_secret, signature_type='auth_header')

        if app_key and app_secret and oauth_token and oauth_token_secret:
            self.auth = OAuth1(self.app_key, self.app_secret,
                               self.oauth_token, self.oauth_token_secret,
                               signature_type='auth_header')

        if self.auth is not None:
            self.client = requests.session(headers=self.headers, auth=self.auth,
                                           config=requests_config)

    def get_authentication_tokens(self):
        """ So, you want to get an authentication url?

            t = Tumblpy(YOUR_CONFIG)
            auth_props = t.get_authentication_tokens()
            auth_url = auth_props['auth_url']
            print auth_url
        """
        request_args = {}
        if self.callback_url:
            request_args['oauth_callback'] = self.callback_url

        response = self.client.get(self.request_token_url, params=request_args)

        if response.status_code != 200:
            raise TumblpyAuthError('Seems something couldn\'t be verified with your OAuth junk. Error: %s, Message: %s' % (response.status_code, response.content))

        request_tokens = dict(parse_qsl(response.content))
        if not request_tokens:
            raise TumblpyError('Unable to decode request tokens.')

        auth_url_params = {
            'oauth_token': request_tokens['oauth_token'],
            'oauth_callback': self.callback_url
        }

        request_tokens['auth_url'] = self.authenticate_url + '?' + urllib.urlencode(auth_url_params)

        return request_tokens

    def get_authorized_tokens(self, oauth_verifier):
        """Returns authorized tokens after they go through the auth_url phase.
        """
        response = self.client.get(self.access_token_url,
                                    params={'oauth_verifier': oauth_verifier})
        authorized_tokens = dict(parse_qsl(response.content))
        if not authorized_tokens:
            raise TumblpyError('Unable to decode authorized tokens.')

        return authorized_tokens

    def request(self, endpoint, method='GET', blog_url=None,
                extra_endpoints=None, params=None):
        params = params or {}
        method = method.lower()

        if not method in ('get', 'post'):
            raise TumblpyError('Method must be of GET or POST')

        url = self.api_url  # http://api.tumblr.com/v2/

        if blog_url is not None:
            # http://api.tumblr.com/v2/blog/blogname.tumblr.com/
            blog_url = blog_url.rstrip('/')
            if blog_url.startswith('http://'):
                blog_url = blog_url[7:]

            url = '%sblog/%s/' % (self.api_url, blog_url)

        url = '%s%s' % (url, endpoint)
        if extra_endpoints is not None:
            # In cases like:
            # http://api.tumblr.com/v2/blog/blogname.tumblr.com/posts/type/
            # 'type' is extra in the url & thought this was the best way
            # Docs: http://www.tumblr.com/docs/en/api/v2#posts

            url = '%s/%s' % (url, '/'.join(extra_endpoints))

        params, files = _split_params_and_files(params)
        params.update(self.default_params)

        func = getattr(self.client, method)
        try:
            if method == 'get':
                response = func(url, params=params, headers=self.headers,
                                allow_redirects=False)
            else:
                response = func(url,
                                data=params,
                                files=files,
                                headers=self.headers,
                                allow_redirects=False)

        except requests.exceptions.RequestException:
            raise TumblpyError('An unknown error occurred.')

        if response.status_code == 401:
            raise TumblpyAuthError('Error: %s, Message: %s' % (response.status_code, response.content))

        try:
            if endpoint == 'avatar':
                content = {
                    'response': {
                        'url': response.headers.get('location')
                    }
                }
            else:
                content = json.loads(response.content)
        except ValueError:
            raise TumblpyError('Unable to parse response, invalid JSON.')

        try:
            content = content.get('response', {})
        except AttributeError:
            raise TumblpyError('Unable to parse response, invalid content returned: %s' % content)

        if response.status_code < 200 or response.status_code > 301:
            error_message = ''
            if content and (content.get('errors') or content.get('error')):
                if 'errors' in content:
                    for error in content['errors']:
                        error_message = '%s ' % error
                elif 'error' in content:
                    error_message = content['error']

            error_message = error_message or \
                            'There was an error making your request.'
            raise TumblpyError(error_message, error_code=response.status_code)

        return content

    def get(self, endpoint, blog_url=None, extra_endpoints=None, params=None):
        return self.request(endpoint, blog_url=blog_url,
                            extra_endpoints=extra_endpoints, params=params)

    def post(self, endpoint, blog_url=None, extra_endpoints=None, params=None):
        return self.request(endpoint, method='POST', blog_url=blog_url,
                            extra_endpoints=extra_endpoints, params=params)

    def get_avatar_url(self, blog_url, size=64):
        size = [str(size)] or ['64']
        return self.get('avatar', blog_url=blog_url, extra_endpoints=size)

    def __repr__(self):
        return u'<TumblrAPI: %s>' % self.app_key
