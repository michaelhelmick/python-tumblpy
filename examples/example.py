import sys

from tumblpy import Tumblpy

key = raw_input('App Consumer Key: ')
secret = raw_input('App Consumer Secret: ')

if not 'skip-auth' in sys.argv:
    t = Tumblpy(key, secret)

    callback_url = raw_input('Callback URL: ')

    auth_props = t.get_authentication_tokens(callback_url=callback_url)
    auth_url = auth_props['auth_url']

    OAUTH_TOKEN_SECRET = auth_props['oauth_token_secret']

    print('Connect with Tumblr via: {}'.format(auth_url))

    oauth_token = raw_input('OAuth Token (from callback url): ')
    oauth_verifier = raw_input('OAuth Verifier (from callback url): ')

    t = Tumblpy(key, secret, oauth_token, OAUTH_TOKEN_SECRET)

    authorized_tokens = t.get_authorized_tokens(oauth_verifier)

    final_oauth_token = authorized_tokens['oauth_token']
    final_oauth_token_secret = authorized_tokens['oauth_token_secret']

    print('OAuth Token: {}'.format(final_oauth_token))
    print('OAuth Token Secret: {}'.format(final_oauth_token_secret))
else:
    final_oauth_token = raw_input('OAuth Token: ')
    final_oauth_token_secret = raw_input('OAuth Token Secret: ')

t = Tumblpy(key, secret, final_oauth_token, final_oauth_token_secret)

blog_url = t.post('user/info')
blog_url = blog_url['user']['blogs'][0]['url']

print('Your blog url is: {}'.format(blog_url))

posts = t.posts(blog_url)

print('Here are some posts this blog has made:', posts)

# print t.post('post', blog_url=blog_url, params={'type':'text', 'title': 'Test', 'body': 'Lorem ipsum.'})
