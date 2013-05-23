.. :changelog:

History
-------

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