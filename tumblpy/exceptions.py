class TumblpyError(Exception):
    """Generic error class, catch-all for most Tumblpy issues.
    from tumblpy import TumblpyError, TumblpyRateLimitError, TumblpyAuthError
    """
    def __init__(self, msg, error_code=None):
        self.error_code = error_code
        if error_code is not None:
            if error_code == 503:
                raise TumblpyRateLimitError(msg, error_code)
            elif error_code == 401:
                raise TumblpyAuthError(msg, error_code)

        super(TumblpyError, self).__init__(msg)

    @property
    def msg(self):
        return self.args[0]


class TumblpyRateLimitError(TumblpyError):
    """Raised when you've hit an API limit."""
    pass


class TumblpyAuthError(TumblpyError):
    """Raised when you try to access a protected resource and it fails due to
     some issue with your authentication."""
    pass
