#     ______                __    __
#    /_  __/_  ______ ___  / /_  / /___  __  __
#     / / / / / / __ `__ \/ __ \/ / __ \/ / / /
#    / / / /_/ / / / / / / /_/ / / /_/ / /_/ /
#   /_/  \__,_/_/ /_/ /_/_.___/_/ .___/\__, /
#                              /_/    /____/

"""
Tumblpy
-------

Tumblpy is a Python library to help interface with the Tumblr API and OAuth
"""

__author__ = 'Mike Helmick <mikehelmick@me.com>'
__version__ = '1.0.5'

from .api import Tumblpy
from .exceptions import (
    TumblpyError, TumblpyAuthError, TumblpyRateLimitError
)
