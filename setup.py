# -*- coding: utf-8 -*-

#  Quickstarted Options:
#
#  sqlalchemy: True
#  auth:       sqlalchemy
#  mako:       False
#
#

# This is just a work-around for a Python2.7 issue causing
# interpreter crash at exit when trying to log an info message.
try:
    import logging
    import multiprocessing
except:
    pass

import sys
py_version = sys.version_info[:2]

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

testing = [
    'WebTest >= 1.2.3',
    'nose',
    'nose-exclude',
    'coverage',
    'tg.devtools',
    'tox',
    'pymongo',
    'mock',
    'selenium'
]

install_requires = [
    "TurboGears2",
    "Beaker",
    "Genshi",
    "zope.sqlalchemy>=1.2",
    "sqlalchemy>=1.3.12",  # should work even with older versions
    "alembic>=1.0",
    "repoze.who",
    "tw2.forms",
    "tgext.admin >= 0.6.1",
    "WebHelpers2",
    "cython",
    "tgext.evolve >= 0.0.5",
    "numexpr",
    "requests == 2.20.0",
    "axf == 0.0.19",
    "kajiki >= 0.8.0",  # at least this version for python3.8 support
    "tgext.pluggable",
    "tgext.webassets",
    "rjsmin",
    "rcssmin",
    "tgapp-categories == 0.3.1",  # 0.4.0 introduces nested categories, we should upgrade
]

if py_version != (3, 2):
    # Babel not available on 3.2
    install_requires.append("Babel")

if py_version[0] < 3:
    install_requires.append("pandas == 0.24.2")  # latest version for python2
else:
    install_requires.append('pandas >= 1.0')

if py_version[0] < 3:
    # you actually need to replace js and add css in public directory
    install_requires.append("bokeh == 1.0.4")
else:
    install_requires.append("bokeh == 2.1.1")

setup(
    name='etl',
    version='0.1',
    description='',
    author='',
    author_email='',
    url='',
    packages=find_packages(exclude=['ez_setup']),
    install_requires=install_requires,
    extras_require={
        'testing': testing,
    },
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=testing,
    package_data={'etl': [
        'i18n/*/LC_MESSAGES/*.mo',
        'templates/*/*',
        'public/*/*'
    ]},
    message_extractors={'etl': [
        ('**.py', 'python', None),
        ('templates/**.html', 'genshi', None),
        ('public/**', 'ignore', None)
    ]},
    entry_points={
        'paste.app_factory': [
            'main = etl.config.middleware:make_app'
        ],
        'gearbox.plugins': [
            'turbogears-devtools = tg.devtools'
        ]
    },
    zip_safe=False
)
