Tumblpy
=======

.. image:: https://pypip.in/d/python-tumblpy/badge.png
        :target: https://crate.io/packages/python-tumblpy/

Tumblpy is a Python library to help interface with Tumblr v2 REST API & OAuth

Features
--------

* Retrieve user information and blog information
* Common Tumblr methods
   - Posting blog posts
   - Unfollowing/following blogs
   - Edit/delete/reblog posts
   - And many more!!
* Photo Uploading
* Transparent *Python 3* Support!


Installation
------------

Installing Tumbply is simple:
::

    $ pip install python-tumblpy


Usage
-----

Importing
~~~~~~~~~

.. code-block:: python

    from tumblpy import Tumblpy

Authorization URL
~~~~~~~~~~~~~~~~~

.. code-block:: python

    t = Tumblpy(YOUR_CONSUMER_KEY, YOUR_CONSUMER_SECRET)

    auth_props = t.get_authentication_tokens(callback_url='http://michaelhelmick.com')
    auth_url = auth_props['auth_url']

    OAUTH_TOKEN_SECRET = auth_props['oauth_token_secret']

    print 'Connect with Tumblr via: %s' % auth_url

Once you click "Allow" be sure that there is a URL set up to handle getting finalized tokens and possibly adding them to your database to use their information at a later date.

Handling the Callback
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # OAUTH_TOKEN_SECRET comes from the previous step
    # if needed, store those in a session variable or something

    # oauth_verifier and OAUTH_TOKEN are found in your callback url querystring
    # In Django, you'd do something like
    # OAUTH_TOKEN = request.GET.get('oauth_token')
    # oauth_verifier = request.GET.get('oauth_verifier')


    t = Tumblpy(YOUR_CONSUMER_KEY, YOUR_CONSUMER_SECRET,
                OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

    authorized_tokens = t.get_authorized_tokens(oauth_verifier)

    final_oauth_token = authorized_tokens['oauth_token']
    final_oauth_token_secret = authorized_tokens['oauth_token_secret']

    # Save those tokens to the database for a later use?

Getting some User information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get the final tokens from the database or wherever you have them stored

    t = Tumblpy(YOUR_CONSUMER_KEY, YOUR_CONSUMER_SECRET,
                OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

    # Print out the user info, let's get the first blog url...
    blog_url = t.post('user/info')
    blog_url = blog_url['user']['blogs'][0]['url']

Getting posts from a certain blog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Assume you are using the blog_url and Tumblpy instance from the previous section
    posts = t.get('posts', blog_url=blog_url)
    print posts
    # or you could use the `posts` method
    audio_posts = t.posts(blog_url, 'audio')
    print audio_posts
    all_posts = t.posts(blog_url)
    print all_posts

Creating a post with a photo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    # Assume you are using the blog_url and Tumblpy instance from the previous sections

    photo = open('/path/to/file/image.png', 'rb')
    post = t.post('post', blog_url=blog_url, params={'type':'photo', 'caption': 'Test Caption', 'data': photo})
    print post  # returns id if posted successfully

Posting an Edited Photo *(This example resizes a photo)*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Assume you are using the blog_url and Tumblpy instance from the previous sections

    # Like I said in the previous section, you can pass any object that has a
    # read() method

    # Assume you are working with a JPEG

    from PIL import Image
    from StringIO import StringIO

    photo = Image.open('/path/to/file/image.jpg')

    basewidth = 320
    wpercent = (basewidth / float(photo.size[0]))
    height = int((float(photo.size[1]) * float(wpercent)))
    photo = photo.resize((basewidth, height), Image.ANTIALIAS)

    image_io = StringIO.StringIO()
    photo.save(image_io, format='JPEG')

    image_io.seek(0)

    try:
        post = t.post('post', blog_url=blog_url, params={'type':'photo', 'caption': 'Test Caption', 'data': photo})
        print post
    except TumblpyError, e:
        # Maybe the file was invalid?
        print e.message

Following a user
~~~~~~~~~~~~~~~~

.. code-block:: python

    # Assume you are using the blog_url and Tumblpy instance from the previous sections
    try:
        follow = t.post('user/follow', params={'url': 'tumblpy.tumblr.com'})
    except TumblpyError:
        # if the url given in params is not valid,
        # Tumblr will respond with a 404 and Tumblpy will raise a TumblpyError

Get a User Avatar URL *(No need for authentication for this method)*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    t = Tumblpy()
    avatar = t.get_avatar_url(blog_url='tumblpy.tumblr.com', size=128)
    print avatar['url']

    # OR

    avatar = t.get('avatar', blog_url='tumblpy.tumblr.com', extra_endpoints=['128'])
    print avatar['url']

Catching errors
~~~~~~~~~~~~~~~

.. code-block:: python

    try:
        t.post('user/info')
    except TumbplyError, e:
        print e.message
        print 'Something bad happened :('

Thanks for using Tumblpy!
