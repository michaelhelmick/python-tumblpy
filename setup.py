#!/usr/bin/env python

import os
import sys

from setuptools import setup

__author__ = 'Mike Helmick <me@michaelhelmick.com>'
__version__ = '1.1.2'

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

setup(
    name='python-tumblpy',
    version=__version__,
    install_requires=['requests>=1.2.2', 'requests_oauthlib>=0.3.2'],
    author='Mike Helmick',
    author_email='me@michaelhelmick.com',
    license=open('LICENSE').read(),
    url='https://github.com/michaelhelmick/python-tumblpy/',
    keywords='python tumblpy tumblr oauth api',
    description='A Python Library to interface with Tumblr v2 REST API & OAuth',
    long_description=open('README.rst').read() + '\n\n' +
                     open('HISTORY.rst').read(),
    download_url='https://github.com/michaelhelmick/python-tumblpy/zipball/master',
    include_package_data=True,
    packages=['tumblpy'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Communications :: Chat',
        'Topic :: Internet'
    ],
)
