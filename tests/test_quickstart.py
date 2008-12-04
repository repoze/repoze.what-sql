# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008, Gustavo Narea <me@gustavonarea.net>
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################

"""
Tests for the repoze.what SQL quickstart.

"""

import unittest

from repoze.who.plugins.basicauth import BasicAuthPlugin
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
from repoze.who.plugins.form import RedirectingFormPlugin
from repoze.who.tests import Base as BasePluginTester, DummyApp

from repoze.what.middleware import AuthorizationMetadata
from repoze.what.plugins.quickstart import setup_sql_auth, \
                                           SQLAuthenticatorPlugin

import databasesetup
from fixture.model import User, Group, Permission, DBSession


class TestSetupAuth(BasePluginTester):
    """Tests for the setup_sql_auth() function"""
    
    def setUp(self):
        super(TestSetupAuth, self).setUp()
        databasesetup.setup_database()
    
    def tearDown(self):
        super(TestSetupAuth, self).tearDown()
        databasesetup.teardownDatabase()
    
    def _in_registry(self, app, registry_key, registry_type):
        assert registry_key in app.name_registry, ('Key "%s" not in registry' %
                                                   registry_key)
        assert isinstance(app.name_registry[registry_key], registry_type), \
               'Registry key "%s" is of type "%s" (not "%s")' % \
               (registry_key, app.name_registry[registry_key].__class__.__name__,
                registry_type.__name__)
    
    def _makeApp(self, **who_args):
        app_with_auth = setup_sql_auth(DummyApp(), User, Group, Permission,
                                       DBSession, **who_args)
        return app_with_auth

    def test_no_extras(self):
        app = self._makeApp()
        self._in_registry(app, 'main_identifier', RedirectingFormPlugin)
        self._in_registry(app, 'authorization_md', AuthorizationMetadata)
        self._in_registry(app, 'cookie', AuthTktCookiePlugin)
        self._in_registry(app, 'sqlauth', SQLAuthenticatorPlugin)
        self._in_registry(app, 'form', RedirectingFormPlugin)
    
    def test_form_doesnt_identify(self):
        app = self._makeApp(form_identifies=False)
        assert 'main_identifier' not in app.name_registry
    
    def test_additional_identifiers(self):
        identifiers = [('http_auth', BasicAuthPlugin('1+1=2'))]
        app = self._makeApp(identifiers=identifiers)
        self._in_registry(app, 'main_identifier', RedirectingFormPlugin)
        self._in_registry(app, 'http_auth', BasicAuthPlugin)
    
    def test_non_default_form_plugin(self):
        app = self._makeApp(form_plugin=BasicAuthPlugin('1+1=2'))
        self._in_registry(app, 'main_identifier', BasicAuthPlugin)
