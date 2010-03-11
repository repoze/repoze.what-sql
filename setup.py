# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007, Agendaless Consulting and Contributors.
# Copyright (c) 2008, Florent Aide <florent.aide@gmail.com>.
# Copyright (c) 2008-2009, Gustavo Narea <me@gustavonarea.net>.
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################

import os

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
version = open(os.path.join(here, 'VERSION.txt')).readline().rstrip()

setup(name='repoze.what.plugins.sql',
      version=version,
      description=('The repoze.what SQL plugin'),
      long_description=README,
      classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Database",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Security"
        ],
      keywords='web application wsgi server wsgi sql sqlalchemy elixir '\
               'authorization repoze',
      author='Gustavo Narea',
      author_email='repoze-dev@lists.repoze.org',
      namespace_packages = ['repoze', 'repoze.what', 'repoze.what.plugins'],
      url='http://what.repoze.org/docs/plugins/sql/',
      license='BSD-derived (http://www.repoze.org/LICENSE.txt)',
      packages=find_packages(exclude=["tests", "tests.*", "test_elixir"]),
      package_data={'': ['VERSION.txt', 'README.txt']},
      include_package_data=True,
      zip_safe=False,
      tests_require=['repoze.what', 'sqlalchemy >= 0.5', 'coverage', 'nose'],
      install_requires=[
          'repoze.what >= 1.0.3',
          'sqlalchemy >= 0.5',
          ],
      test_suite='nose.collector',
      entry_points = """\
      """
      )

