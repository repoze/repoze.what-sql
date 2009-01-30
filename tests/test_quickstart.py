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
from urllib import quote as original_quoter

from paste.httpexceptions import HTTPFound

from repoze.who.plugins.basicauth import BasicAuthPlugin
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
from repoze.who.plugins.form import RedirectingFormPlugin
from repoze.who.plugins.sa import SQLAlchemyAuthenticatorPlugin, \
                                  SQLAlchemyUserMDPlugin
from repoze.who.tests import Base as BasePluginTester, DummyApp

from repoze.what.middleware import AuthorizationMetadata
from repoze.what.plugins.quickstart import setup_sql_auth, \
                                           find_plugin_translations, \
                                           FriendlyRedirectingFormPlugin

import databasesetup
from fixture.model import User, Group, Permission, DBSession


# Let's prevent the original quote() from leaving slashes:
quote = lambda txt: original_quoter(txt, '')


class TestFriendlyRedirectingFormPlugin(TestCase):
    
    def test_constructor(self):
        p = self._make_one()
        self.assertEqual(p.login_counter_name, '__logins')
        self.assertEqual(p.post_login_url, None)
        self.assertEqual(p.post_logout_url, None)
    
    def test_login_without_postlogin_page(self):
        """
        The page to be redirected to after login must include the login 
        counter.
        
        """
        # --- Configuring the plugin:
        p = self._make_one()
        # --- Configuring the mock environ:
        came_from = '/some_path'
        environ = self._make_environ('/login_handler',
                                     'came_from=%s' % quote(came_from))
        # --- Testing it:
        p.identify(environ)
        app = environ['repoze.who.application']
        new_redirect = came_from + '?__logins=0'
        self.assertEqual(app.location(), new_redirect)
    
    def test_post_login_page_as_url(self):
        """Post-logout pages can also be defined as URLs, not only paths"""
        # --- Configuring the plugin:
        login_url = 'http://example.org/welcome'
        p = self._make_one(post_login_url=login_url)
        # --- Configuring the mock environ:
        environ = self._make_environ('/login_handler')
        # --- Testing it:
        p.identify(environ)
        app = environ['repoze.who.application']
        self.assertEqual(app.location(), login_url + '?__logins=0')
    
    def test_post_login_page_with_script_path(self):
        """
        While redirecting to the post-login page, the SCRIPT_PATH must be
        taken into account.
        
        """
        # --- Configuring the plugin:
        p = self._make_one(post_login_url='/welcome_back')
        # --- Configuring the mock environ:
        environ = self._make_environ('/login_handler', script_path='/my-app')
        # --- Testing it:
        p.identify(environ)
        app = environ['repoze.who.application']
        self.assertEqual(app.location(), '/my-app/welcome_back?__logins=0')
    
    def test_post_login_page_with_script_path_and_came_from(self):
        """
        While redirecting to the post-login page with the came_from variable, 
        the SCRIPT_PATH must be taken into account.
        
        """
        # --- Configuring the plugin:
        p = self._make_one(post_login_url='/welcome_back')
        # --- Configuring the mock environ:
        came_from = '/something'
        environ = self._make_environ('/login_handler',
                                     'came_from=%s' % quote(came_from),
                                     script_path='/my-app')
        # --- Testing it:
        p.identify(environ)
        app = environ['repoze.who.application']
        redirect = '/my-app/welcome_back?__logins=0&came_from=%s'
        self.assertEqual(app.location(), redirect % quote(came_from))
    
    def test_post_login_page_without_login_counter(self):
        """
        If there's no login counter defined, the post-login page should receive
        the counter at zero.
        
        """
        # --- Configuring the plugin:
        p = self._make_one(post_login_url='/welcome_back')
        # --- Configuring the mock environ:
        environ = self._make_environ('/login_handler')
        # --- Testing it:
        p.identify(environ)
        app = environ['repoze.who.application']
        self.assertEqual(app.location(), '/welcome_back?__logins=0')
    
    def test_post_login_page_with_login_counter(self):
        """
        If the login counter is defined, the post-login page should receive it
        as is.
        
        """
        # --- Configuring the plugin:
        p = self._make_one(post_login_url='/welcome_back')
        # --- Configuring the mock environ:
        environ = self._make_environ('/login_handler', '__logins=2',
                                     redirect='/some_path')
        # --- Testing it:
        p.identify(environ)
        app = environ['repoze.who.application']
        self.assertEqual(app.location(), '/welcome_back?__logins=2')
    
    def test_post_login_page_with_invalid_login_counter(self):
        """
        If the login counter is defined with an invalid value, the post-login 
        page should receive the counter at zero.
        
        """
        # --- Configuring the plugin:
        p = self._make_one(post_login_url='/welcome_back')
        # --- Configuring the mock environ:
        environ = self._make_environ('/login_handler', '__logins=non_integer',
                                     redirect='/some_path')
        # --- Testing it:
        p.identify(environ)
        app = environ['repoze.who.application']
        self.assertEqual(app.location(), '/welcome_back?__logins=0')
    
    def test_post_login_page_with_referrer(self):
        """
        If the referrer is defined, it should be passed along with the login
        counter to the post-login page.
        
        """
        # --- Configuring the plugin:
        p = self._make_one(post_login_url='/welcome_back')
        # --- Configuring the mock environ:
        orig_redirect = '/some_path'
        came_from = quote('http://example.org')
        environ = self._make_environ(
            '/login_handler',
            '__logins=3&came_from=%s' % came_from,
            redirect=orig_redirect,
            )
        # --- Testing it:
        p.identify(environ)
        app = environ['repoze.who.application']
        new_url = '/welcome_back?__logins=3&came_from=%s' % came_from
        self.assertEqual(app.location(), new_url)
    
    def test_login_page_with_login_counter(self):
        """
        In the page where the login form is displayed, the login counter
        must be defined in the WSGI environment variable 'repoze.who.logins'.
        
        """
        # --- Configuring the plugin:
        p = self._make_one()
        # --- Configuring the mock environ:
        environ = self._make_environ('/login', '__logins=2')
        # --- Testing it:
        p.identify(environ)
        self.assertEqual(environ['repoze.who.logins'], 2)
        self.assertEqual(environ['QUERY_STRING'], '')
    
    def test_login_page_without_login_counter(self):
        """
        In the page where the login form is displayed, the login counter
        must be defined in the WSGI environment variable 'repoze.who.logins' 
        and if it's not defined in the query string, set it to zero in the
        environ.
        
        """
        # --- Configuring the plugin:
        p = self._make_one()
        # --- Configuring the mock environ:
        environ = self._make_environ('/login')
        # --- Testing it:
        p.identify(environ)
        self.assertEqual(environ['repoze.who.logins'], 0)
        self.assertEqual(environ['QUERY_STRING'], '')
    
    def test_login_page_with_camefrom(self):
        """
        In the page where the login form is displayed, the login counter
        must be defined in the WSGI environment variable 'repoze.who.logins' 
        and hidden in the query string available in the environ.
        
        """
        # --- Configuring the plugin:
        p = self._make_one()
        # --- Configuring the mock environ:
        came_from = 'http://example.com'
        environ = self._make_environ('/login',
                                     'came_from=%s' % quote(came_from))
        # --- Testing it:
        p.identify(environ)
        self.assertEqual(environ['repoze.who.logins'], 0)
        self.assertEqual(environ['QUERY_STRING'], 
                         'came_from=%s' % quote(came_from))
    
    def test_logout_without_post_logout_page(self):
        """
        Users must be redirected to '/' on logout if there's no referrer page
        and no post-logout page defined.
        
        """
        # --- Configuring the plugin:
        p = self._make_one()
        # --- Configuring the mock environ:
        environ = self._make_environ('/logout_handler')
        # --- Testing it:
        app = p.challenge(environ, '401 Unauthorized', [('app', '1')],
                          [('forget', '1')])
        self.assertEqual(app.location(), '/')
    
    def test_logout_with_script_path_and_without_post_logout_page(self):
        """
        Users must be redirected to SCRIPT_PATH on logout if there's no 
        referrer page and no post-logout page defined.
        
        """
        # --- Configuring the plugin:
        p = self._make_one()
        # --- Configuring the mock environ:
        environ = self._make_environ('/logout_handler', script_path='/my-app')
        # --- Testing it:
        app = p.challenge(environ, '401 Unauthorized', [('app', '1')],
                          [('forget', '1')])
        self.assertEqual(app.location(), '/my-app')
    
    def test_logout_with_camefrom_and_without_post_logout_page(self):
        """
        Users must be redirected to the referrer page on logout if there's no
        post-logout page defined.
        
        """
        # --- Configuring the plugin:
        p = self._make_one()
        # --- Configuring the mock environ:
        environ = self._make_environ('/logout_handler')
        environ['came_from'] = '/somewhere'
        # --- Testing it:
        app = p.challenge(environ, '401 Unauthorized', [('app', '1')],
                          [('forget', '1')])
        self.assertEqual(app.location(), '/somewhere')
    
    def test_logout_with_post_logout_page(self):
        """Users must be redirected to the post-logout page, if defined"""
        # --- Configuring the plugin:
        p = self._make_one(post_logout_url='/see_you_later')
        # --- Configuring the mock environ:
        environ = self._make_environ('/logout_handler')
        # --- Testing it:
        app = p.challenge(environ, '401 Unauthorized', [('app', '1')],
                          [('forget', '1')])
        self.assertEqual(app.location(), '/see_you_later')
    
    def test_logout_with_post_logout_page_as_url(self):
        """Post-logout pages can also be defined as URLs, not only paths"""
        # --- Configuring the plugin:
        logout_url = 'http://example.org/see_you_later'
        p = self._make_one(post_logout_url=logout_url)
        # --- Configuring the mock environ:
        environ = self._make_environ('/logout_handler')
        # --- Testing it:
        app = p.challenge(environ, '401 Unauthorized', [('app', '1')],
                          [('forget', '1')])
        self.assertEqual(app.location(), logout_url)
    
    def test_logout_with_post_logout_page_and_script_path(self):
        """
        Users must be redirected to the post-logout page, if defined, taking
        the SCRIPT_PATH into account.
        
        """
        # --- Configuring the plugin:
        p = self._make_one(post_logout_url='/see_you_later')
        # --- Configuring the mock environ:
        environ = self._make_environ('/logout_handler', script_path='/my-app')
        # --- Testing it:
        app = p.challenge(environ, '401 Unauthorized', [('app', '1')],
                          [('forget', '1')])
        self.assertEqual(app.location(), '/my-app/see_you_later')
    
    def test_logout_with_post_logout_page_and_came_from(self):
        """
        Users must be redirected to the post-logout page, if defined, and also
        pass the came_from variable.
        
        """
        # --- Configuring the plugin:
        p = self._make_one(post_logout_url='/see_you_later')
        # --- Configuring the mock environ:
        came_from = '/the-path'
        environ = self._make_environ('/logout_handler')
        environ['came_from'] = came_from
        # --- Testing it:
        app = p.challenge(environ, '401 Unauthorized', [('app', '1')],
                          [('forget', '1')])
        redirect = '/see_you_later?came_from=%s'
        self.assertEqual(app.location(), redirect % quote(came_from))
    
    def test_failed_login(self):
        """
        Users must be redirected to the login form if the tried to log in with
        the wrong credentials.
        
        """
        # --- Configuring the plugin:
        p = self._make_one()
        # --- Configuring the mock environ:
        environ = self._make_environ('/somewhere')
        environ['repoze.who.logins'] = 1
        # --- Testing it:
        app = p.challenge(environ, '401 Unauthorized', [('app', '1')],
                          [('forget', '1')])
        came_from = 'http://example.org/somewhere'
        redirect = '/login?__logins=2&came_from=%s' % quote(came_from)
        self.assertEqual(app.location(), redirect)
    
    def test_not_logout_and_not_failed_logins(self):
        """
        Do not modify the challenger unless it's handling a logout or a
        failed login.
        
        """
        # --- Configuring the plugin:
        p = self._make_one()
        # --- Configuring the mock environ:
        environ = self._make_environ('/somewhere')
        # --- Testing it:
        app = p.challenge(environ, '401 Unauthorized', [('app', '1')],
                          [('forget', '1')])
        came_from = 'http://example.org/somewhere'
        redirect = '/login?came_from=%s' % quote(came_from)
        self.assertEqual(app.location(), redirect)
    
    def _make_one(self, login_counter_name=None, post_login_url=None,
                  post_logout_url=None):
        p = FriendlyRedirectingFormPlugin('/login', '/login_handler',
                                          '/logout_handler', 'whatever',
                                          login_counter_name=login_counter_name,
                                          post_login_url=post_login_url,
                                          post_logout_url=post_logout_url)
        return p
    
    def _make_redirection(self, url):
        app = HTTPFound(url)
        return app
    
    def _make_environ(self, path_info, qs='', script_path='', redirect=None):
        environ = {
            'PATH_INFO': path_info,
            'SCRIPT_PATH': script_path,
            'QUERY_STRING': qs,
            'SERVER_NAME': 'example.org',
            'SERVER_PORT': '80',
            'wsgi.input': '',
            'wsgi.url_scheme': 'http',
            }
        if redirect:
            environ['repoze.who.application'] = self._make_redirection(redirect)
        return environ


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
        post_login_url = '/myapp/welcome_back'
        logout_handler = '/myapp/logout'
        post_logout_url = '/myapp/see_you_later'
        login_counter_name = '__failed_logins'
        app = self._makeApp(login_url=login_url, login_handler=login_handler,
                            logout_handler=logout_handler,
                            post_login_url=post_login_url,
                            post_logout_url=post_logout_url,
                            login_counter_name=login_counter_name)
        form = app.name_registry['form']
        self.assertEqual(form.login_form_url, login_url)
        self.assertEqual(form.login_handler_path, login_handler)
        self.assertEqual(form.post_login_url, post_login_url)
        self.assertEqual(form.logout_handler_path, logout_handler)
        self.assertEqual(form.post_logout_url, post_logout_url)
        self.assertEqual(form.login_counter_name, login_counter_name)


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
