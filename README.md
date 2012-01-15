#Overview
Couldn't find a nice clean class that I liked to interact with Tumblr v2 API. Some help from [ryanmcgrath twython class](https://github.com/ryanmcgrath/twython), thanks a lot. Reading over some of that code helped a lot!
Hope this documentation explains everything you need to get started. Any questions feel free to email me or inbox me.

#Authorization URL
*Get an authorization url for your user*

```python
t = Tumblpy(app_key = '*your app key*',
            app_secret = '*your app secret*')

auth_props = t.get_authentication_tokens()
auth_url = auth_props['auth_url']

oauth_token = auth_props['oauth_token']
oauth_token_secret = auth_props['oauth_token_secret']

Connect with Tumblr via: % auth_url
```

Once you click "Allow" be sure that there is a URL set up to handle getting finalized tokens and possibly adding them to your database to use their information at a later date.

#Handling the callback
```python
t = Tumblpy(app_key = '*your app key*',
            app_secret = '*your app secret*',
            oauth_token=session['tumblr_session_keys']['oauth_token'],
            oauth_token_secret=session['tumblr_session_keys']['oauth_token_secret'])

# In Django, you'd do something like
# oauth_verifier = request.GET.get('oauth_verifier')

oauth_verifier = *Grab oauth verifier from URL*
authorized_tokens = t.get_access_token(oauth_verifier)

final_oauth_token = authorized_tokens['oauth_token']
final_oauth_token_secret = authorized_tokens['oauth_token_secret']

# Save those tokens to the database for a later use?
```

#Getting some user information
```python
# Get the final tokens from the database or wherever you have them stored

t = Tumblpy(app_key = '*your app key*',
            app_secret = '*your app secret*',
            oauth_token=final_tokens['oauth_token'],
            oauth_token_secret=final_tokens['oauth_token_secret'])

# Print out the user info, let's get the first blog url...
blog_url = t.post('user/info')
blog_url = blog_url['user']['blogs'][0]['url']

# Let's get their blog posts for that URL
posts = t.get('posts', blog_url=blog_url)

print posts
```