#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages
import os

execfile('./src/django_webid/auth/__init__.py')
VERSION = __version__

setup_root = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(setup_root, "src"))

long_description = "A django app to enable WebID authentication."


packages = find_packages('src')
setup(
    name='django-webid-auth',
    package_dir={'': 'src'},
    packages=packages,
    namespace_packages=['django_webid'],
    include_package_data=True,
    exclude_package_data={
        'requirements': ['%s/*.tar.gz' % VERSION],
    },
    version=VERSION,
    description="""A django app to enable WebID authentication.""",
    long_description=long_description,
    author='Ben Carrillo',
    author_email='bennomadic@gmail.com',
    download_url='https://github.com/bennomadic/django-webid-auth.git',
    install_requires=['django-webid-provider>=0.2'],
    #XXX how to mark dependencies from git?
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: JavaScript',
        'Framework :: Django',
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    #test_requires=[],
    keywords='foaf, ssl, webid, x509, certificate, client certificate,\
    authentication, authorization, django',
    zip_safe=False,
)
