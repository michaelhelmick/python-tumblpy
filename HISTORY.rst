.. :changelog:

History
-------

1.1.4 (2016-02-08)
++++++++++++++++++

- Remove old api url string formatting.
- Added ``posts`` method to Tumblpy, see README for example.

1.1.3 (2016-01-17)
++++++++++++++++++

- Fix missing import

1.1.2 (2016-12-22)
++++++++++++++++++

- Fix missing import

1.1.1 (2016-05-12)
++++++++++++++++++

- Fix issue where blogs using https:// were being parsed wrong


1.1.0 (2016-30-04)
++++++++++++++++++

- Add following and dashboard API methods


1.0.5 (2015-08-13)
++++++++++++++++++

- Add support for ``proxies`` keyword for requests


1.0.4 (2015-01-15)
++++++++++++++++++

- Fix request token decode issue in Python 3


1.0.3 (2014-10-17)
++++++++++++++++++

- Unpin ``requests`` and ``requests-oauthlib`` versions in ``setup.py``


1.0.2 (2013-05-31)
++++++++++++++++++

- Made the hotfix for posting photos a little more hotfixy... fixed posting just regular posts (as well as photos)

1.0.1 (2013-05-29)
++++++++++++++++++

- Hotfix image uploading (not sure why we have to pass ``params`` AND ``data`` to the POST, hotfix for the time being...)
- Allow for ints and floats (and longs in Python 2) to be passed as parameters to Tumblpy Tumblr API functions


1.0.0 (2013-05-23)
++++++++++++++++++

- Changed internal Tumblpy API structure, but Tumblpy functions should still work as they did before
- Updated README with more clear examples
- Added LICENSE
- ``_split_params_and_files`` has been moved to ``helpers.py``
- All ``Tumblpy`` exceptions are found in ``exceptions.py``
- Removed ``pool_maxsize`` from ``Tumblpy.__init__`` because it wasn't being used
- Removed ``timeout`` parameter from all request methods for the time being
- Removed ``TumblpyTimeout`` Exception
- Moved ``callback_url`` parameter from ``Tumblpy.__init__`` to ``get_authentication_tokens``
- All authentication and API calls over HTTPS
- Dropped Python 2.5 support
- Full, transparent Python 3.3 support
