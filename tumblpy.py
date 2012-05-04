#!/usr/bin/env python

""" Tumblpy """

__author__ = 'Mike Helmick <mikehelmick@me.com>'
__version__ = '0.5.0'

import urllib
import inspect

try:
    from urlparse import parse_qsl
except ImportError:
    from cgi import parse_qsl

import oauth2 as oauth
import httplib2
import urllib2  # Need this for completing upload requests

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


import mimetypes
import mimetools
import codecs
from io import BytesIO

writer = codecs.lookup('utf-8')[3]


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def iter_fields(fields):
    """Iterate over fields.

    Supports list of (k, v) tuples and dicts.
    """
    if isinstance(fields, dict):
        return ((k, v) for k, v in fields.iteritems())
    return ((k, v) for k, v in fields)

# The following is grabbed from Twython
# Try and gauge the old OAuth2 library spec. Versions 1.5 and greater no longer have the callback
# url as part of the request object; older versions we need to patch for Python 2.5... ugh. ;P
OAUTH_CALLBACK_IN_URL = False
OAUTH_LIB_SUPPORTS_CALLBACK = False
if not hasattr(oauth, '_version') or float(oauth._version.manual_verstr) <= 1.4:
    OAUTH_CLIENT_INSPECTION = inspect.getargspec(oauth.Client.request)
    try:
        OAUTH_LIB_SUPPORTS_CALLBACK = 'callback_url' in OAUTH_CLIENT_INSPECTION.args
    except AttributeError:
        # Python 2.5 doesn't return named tuples, so don't look for an args section specifically.
        OAUTH_LIB_SUPPORTS_CALLBACK = 'callback_url' in OAUTH_CLIENT_INSPECTION
else:
    OAUTH_CALLBACK_IN_URL = True


class TumblpyError(Exception):
    """ Generic error class, catch-all for most Tumblpy issues.

        from Tumblpy import TumblpyError, TumblpyRateLimitError, TumblpyAuthError
    """
    def __init__(self, msg, error_code=None):
        self.msg = msg
        if error_code is not None:
            if error_code == 503:
                raise TumblpyRateLimitError(msg)
            elif error_code == 401:
                raise TumblpyAuthError(msg)

    def __str__(self):
        return repr(self.msg)


class TumblpyRateLimitError(TumblpyError):
    """ Raised when you've hit an API limit.
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
    def __init__(self, app_key=None, app_secret=None, oauth_token=None, oauth_token_secret=None, headers=None, client_args=None, callback_url=None):
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
        self.oauth_token_secret = oauth_token_secret

        self.callback_url = callback_url

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

        if self.oauth_token is not None and self.oauth_token_secret is not None:
            self.token = oauth.Token(key=self.oauth_token, secret=self.oauth_token_secret)

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
        callback_url = self.callback_url

        request_args = {}
        method = 'GET'

        if OAUTH_LIB_SUPPORTS_CALLBACK:
            request_args['oauth_callback'] = callback_url
        else:
            # Thanks @jbouvier for the following hack
            # This is a hack for versions of oauth that don't support the callback url
            request_args['body'] = urllib.urlencode({'oauth_callback': callback_url})
            method = 'POST'

        resp, content = self.client.request(self.request_token_url, method, **request_args)

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

    def api_request(self, endpoint, blog_url=None, method='GET',
                    extra_endpoints=None, params=None, files=None):
        params = params or {}

        # http://api.tumblr.com/v2/
        url = self.api_url

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
            # 'type' is extra in the url and this was the best way I thought to do this.
            # Docs: http://www.tumblr.com/docs/en/api/v2#posts

            url = '%s/%s' % (url, '/'.join(extra_endpoints))

        params.update(self.default_params)

        if method == 'POST':
            if files is not None:
                # When uploading a file, we need to create a fake request
                # to sign parameters that are not multipart before we add
                # the multipart file to the parameters...
                # OAuth is not meant to sign multipart post data
                faux_req = oauth.Request.from_consumer_and_token(self.consumer,
                                                                 token=self.token,
                                                                 http_method="POST",
                                                                 http_url=url,
                                                                 parameters=params)

                faux_req.sign_request(oauth.SignatureMethod_HMAC_SHA1(),
                                      self.consumer,
                                      self.token)

                all_upload_params = dict(parse_qsl(faux_req.to_postdata()))
                # For Tumblr, all media (photos, videos)
                # are sent with the 'data' parameter
                all_upload_params['data'] = (files.name, files.read())
                body, content_type = self.encode_multipart_formdata(all_upload_params)

                self.headers.update({
                    'Content-Type': content_type,
                    'Content-Length': str(len(body))
                })

                req = urllib2.Request(url, body, self.headers)
                try:
                    req = urllib2.urlopen(req)
                except urllib2.HTTPError, e:
                    # Making a fake resp var because urllib2.urlopen doesn't
                    # return a tuple like OAuth2 client.request does
                    resp = {'status': e.code}
                    content = e.read()

                # If no error, assume response was 200
                resp = {'status': 200}
                content = req.read()
            else:
                resp, content = self.client.request(url, 'POST', urllib.urlencode(params), headers=self.headers)
        else:
            url = '%s?%s' % (url, urllib.urlencode(params))
            resp, content = self.client.request(url, 'GET', headers=self.headers)

        try:
            # If it is an avatar we need to check the HEAD of the request
            # for 'content-location' because Tumblr /avatar endpoint redirects
            # you from http://api.tumblr.com/v2/blog/<blog_url>/avatar to
            # an actual url for the image.
            if endpoint == 'avatar':
                r = resp

                # Check if we couldn't find the avatar URL, if we can't
                # build the resp, and content to match our styles
                if r.get('content-location') is None:
                    resp = {'status': 404}

                    content = {
                        'error': 'Unable to get avatar url for %s' % blog_url
                    }
                else:
                    content = {
                        'response': {
                            'url': r['content-location']
                        }
                    }
            else:
                content = json.loads(content)
        except ValueError:
            raise TumblpyError('Invalid JSON, response was unable to be parsed.')

        status = int(resp['status'])  # I don't know why Tumblr doesn't return status as an it, but let's cast it to an int..
        if status < 200 or status >= 300:
            error_message = ''
            if 'response' in content and \
                ('errors' in content['response'] or 'error' in content['response']):
                if 'errors' in content['response']:
                    for error in content['response']['errors']:
                        error_message += '%s ' % error
                elif 'error' in content['response']:
                    error_message = content['response']['error']

            if error_message == '':
                error_message = 'There was an error making your request.'
            raise TumblpyError(error_message, error_code=status)

        return content['response']

    def post(self, endpoint, blog_url=None, extra_endpoints=None, params=None, files=None):
        params = params or {}
        return self.api_request(endpoint, method='POST', blog_url=blog_url,
                                extra_endpoints=extra_endpoints, params=params,
                                files=files)

    def get(self, endpoint, blog_url=None, extra_endpoints=None, params=None):
        params = params or {}
        return self.api_request(endpoint, method='GET', blog_url=blog_url,
                                extra_endpoints=extra_endpoints, params=params)

    def get_avatar_url(self, blog_url=None, size=64):
        if blog_url is None:
            raise TumblpyError('Please provide a blog url to get an avatar for.')

        size = [str(size)] or ['64']

        return self.get('avatar', blog_url=blog_url, extra_endpoints=size)

    # Thanks urllib3 <3
    def encode_multipart_formdata(self, fields, boundary=None):
        """
        Encode a dictionary of ``fields`` using the multipart/form-data mime format.

        :param fields:
            Dictionary of fields or list of (key, value) field tuples.  The key is
            treated as the field name, and the value as the body of the form-data
            bytes. If the value is a tuple of two elements, then the first element
            is treated as the filename of the form-data section.

            Field names and filenames must be unicode.

        :param boundary:
            If not specified, then a random boundary will be generated using
            :func:`mimetools.choose_boundary`.
        """
        body = BytesIO()
        if boundary is None:
            boundary = mimetools.choose_boundary()

        for fieldname, value in iter_fields(fields):
            body.write('--%s\r\n' % (boundary))

            if isinstance(value, tuple):
                filename, data = value
                writer(body).write('Content-Disposition: form-data; name="%s"; '
                                   'filename="%s"\r\n' % (fieldname, filename))
                body.write('Content-Type: %s\r\n\r\n' %
                           (get_content_type(filename)))
            else:
                data = value
                writer(body).write('Content-Disposition: form-data; name="%s"\r\n'
                                   % (fieldname))
                body.write(b'Content-Type: text/plain\r\n\r\n')

            if isinstance(data, int):
                data = str(data)  # Backwards compatibility

            if isinstance(data, unicode):
                writer(body).write(data)
            else:
                body.write(data)

            body.write(b'\r\n')

        body.write('--%s--\r\n' % (boundary))

        content_type = 'multipart/form-data; boundary=%s' % boundary

        return body.getvalue(), content_type
