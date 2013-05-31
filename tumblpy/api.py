import requests
from requests_oauthlib import OAuth1

from . import __version__
from .compat import json, urlencode, parse_qsl
from .exceptions import TumblpyError, TumblpyAuthError
from .helpers import _split_params_and_files


class Tumblpy(object):
    def __init__(self, app_key=None, app_secret=None, oauth_token=None,
                 oauth_token_secret=None, headers=None):

        # Define some API URLs real quick
        self.base_api_url = 'https://api.tumblr.com'
        self.api_version = 'v2'
        self.api_url = '%s/%s/' % (self.base_api_url, self.api_version)

        # Authentication URLs
        self.request_token_url = 'https://www.tumblr.com/oauth/request_token'
        self.access_token_url = 'https://www.tumblr.com/oauth/access_token'
        self.authorize_url = 'https://www.tumblr.com/oauth/authorize'
        self.authenticate_url = 'https://www.tumblr.com/oauth/authorize'

        self.default_params = {'api_key': app_key}

        req_headers = {'User-Agent': 'Tumblpy v' + __version__}
        if headers:
            req_headers.update(headers)

        self.app_key = app_key
        self.app_secret = app_secret
        self.oauth_token = oauth_token
        self.oauth_token_secret = oauth_token_secret

        auth = None
        if self.app_key and self.app_secret:
            if not self.oauth_token and not self.oauth_token_secret:
                auth = OAuth1(self.app_key, self.app_secret)
            else:
                auth = OAuth1(self.app_key, self.app_secret,
                              self.oauth_token, self.oauth_token_secret)

        self.client = requests.Session()
        self.client.headers = req_headers
        self.client.auth = auth

    def get_authentication_tokens(self, callback_url=None):
        """Returns a dict including an authorization URL (auth_url) to direct a user to

            :param callback_url: (optional) Url the user is returned to after they authorize your app (web clients only)
        """

        request_args = {}
        if callback_url:
            request_args['oauth_callback'] = callback_url

        response = self.client.get(self.request_token_url, params=request_args)

        if response.status_code != 200:
            raise TumblpyAuthError('Seems something couldn\'t be verified with your OAuth junk. Error: %s, Message: %s' % (response.status_code, response.content))

        request_tokens = dict(parse_qsl(response.content))
        if not request_tokens:
            raise TumblpyError('Unable to decode request tokens.')

        auth_url_params = {
            'oauth_token': request_tokens['oauth_token'],
        }
        if callback_url:
            auth_url_params['oauth_callback'] = callback_url

        request_tokens['auth_url'] = self.authenticate_url + '?' + urlencode(auth_url_params)

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
                response = func(url, params=params, allow_redirects=False)
            else:
                kwargs = {'data': params, 'files': files, 'allow_redirects': False}
                if files:
                    kwargs['params'] = params
                response = func(url, **kwargs)
        except requests.exceptions.RequestException:
            raise TumblpyError('An unknown error occurred.')

        if response.status_code == 401:
            raise TumblpyAuthError('Error: %s, Message: %s' % (response.status_code, response.content))

        content = response.content.decode('utf-8')
        try:
            if endpoint == 'avatar':
                content = {
                    'response': {
                        'url': response.headers.get('location')
                    }
                }
            else:
                content = json.loads(content)
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

            error_message = (error_message or
                             'There was an error making your request.')
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
