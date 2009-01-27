# -*- coding: utf-8 -*-
##############################################################################
#
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

"""
Tests for the repoze.what SQL quickstart.

"""

from unittest import TestCase

from repoze.who.plugins.basicauth import BasicAuthPlugin
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
from repoze.who.plugins.form import RedirectingFormPlugin
from repoze.who.plugins.sa import SQLAlchemyAuthenticatorPlugin, \
                                  SQLAlchemyUserMDPlugin
from repoze.who.tests import Base as BasePluginTester, DummyApp

from repoze.what.middleware import AuthorizationMetadata
from repoze.what.plugins.quickstart import setup_sql_auth, \
                                           find_plugin_translations

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
        self._in_registry(app, 'sql_user_md', SQLAlchemyUserMDPlugin)
        self._in_registry(app, 'cookie', AuthTktCookiePlugin)
        self._in_registry(app, 'sqlauth', SQLAlchemyAuthenticatorPlugin)
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

    def test_custom_login_urls(self):
        login_url = '/myapp/login'
        login_handler = '/myapp/login_handler'
        logout_handler = '/myapp/logout'
        app = self._makeApp(login_url=login_url, login_handler=login_handler,
                            logout_handler=logout_handler)
        form = app.name_registry['form']
        self.assertEqual(form.login_form_url, login_url)
        self.assertEqual(form.login_handler_path, login_handler)
        self.assertEqual(form.logout_handler_path, logout_handler)


class TestPluginTranslationsFinder(TestCase):
    
    def test_it(self):
        # --- Setting it up ---
        translations = {
            'validate_password': 'pass_checker',
            'user_name': 'member_name',
            'users': 'members',
            'group_name': 'team_name',
            'groups': 'teams',
            'permission_name': 'perm_name',
            'permissions': 'perms'
            }
        plugin_translations = find_plugin_translations(translations)
        # --- Testing it ---
        # Group translations
        group_translations = {
            'item_name': translations['user_name'],
            'items': translations['users'],
            'section_name': translations['group_name'],
            'sections': translations['groups'],
            }
        self.assertEqual(group_translations, 
                         plugin_translations['group_adapter'])
        # Permission translations
        perm_translations = {
            'item_name': translations['group_name'],
            'items': translations['groups'],
            'section_name': translations['permission_name'],
            'sections': translations['permissions'],
            }
        self.assertEqual(perm_translations, 
                         plugin_translations['permission_adapter'])
        # Authenticator translations
        auth_translations = {
            'user_name': translations['user_name'],
            'validate_password': translations['validate_password'],
            }
        self.assertEqual(auth_translations, 
                         plugin_translations['authenticator'])
        # MD Provider translations
        md_translations = {'user_name': translations['user_name']}
        self.assertEqual(md_translations, 
                         plugin_translations['mdprovider'])
