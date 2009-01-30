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

"""
Sample plugins and middleware configuration for :mod:`repoze.who` and
:mod:`repoze.what`.

"""

from urlparse import urlparse, urlunparse
from urllib import urlencode
try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs

from paste.httpexceptions import HTTPFound
from paste.request import construct_url, resolve_relative_url, \
                          parse_dict_querystring
from paste.response import replace_header, header_value

from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
from repoze.who.plugins.form import RedirectingFormPlugin
from repoze.who.plugins.sa import SQLAlchemyAuthenticatorPlugin, \
                                  SQLAlchemyUserMDPlugin

from repoze.what.middleware import setup_auth
from repoze.what.plugins.sql import configure_sql_adapters


#{ repoze.who plugins


class FriendlyRedirectingFormPlugin(RedirectingFormPlugin):
    """
    Make the :class:`RedirectingFormPlugin 
    <repoze.who.plugins.form.RedirectingFormPlugin>` friendlier.
    
    It makes ``RedirectingFormPlugin`` friendlier in the following aspects:
    
    * Users are not challenged on logout, unless the referrer URL is a
      private one (but that's up to the application).
    * Developers may define post-login and/or post-logout pages.
    * In the login URL, the amount of failed logins is available in the
      environ. It's also increased by one on every login try. This counter 
      will allow developers not using a post-login page to handle logins that
      fail/succeed.
    
    You should keep in mind that if you're using a post-login or a post-logout
    page, that page will receive the referrer URL as a query string variable
    whose name is "came_from".
    
    """
    
    def __init__(self, *args, **kwargs):
        """
        Setup the friendly ``RedirectingFormPlugin``.
        
        It receives the same arguments as the parent, plus the following
        *keyword* arguments:
        
        * ``login_counter_name``: The name of the login counter variable
          in the query string. Defaults to ``__logins``.
        * ``post_login_url``: The URL/path to the post-login page, if any.
        * ``post_logout_url``: The URL/path to the post-logout page, if any.
        
        """
        
        # Extracting the keyword arguments for this plugin:
        self.login_counter_name = kwargs.get('login_counter_name')
        self.post_login_url = kwargs.get('post_login_url')
        self.post_logout_url = kwargs.get('post_logout_url')
        if 'login_counter_name' in kwargs:
            del kwargs['login_counter_name']
        if 'post_login_url' in kwargs:
            del kwargs['post_login_url']
        if 'post_logout_url' in kwargs:
            del kwargs['post_logout_url']
        # If the counter name is something useless, like None:
        if not self.login_counter_name:
            self.login_counter_name = '__logins'
        # Finally we can invoke the parent constructor
        super(FriendlyRedirectingFormPlugin, self).__init__(*args, **kwargs)
    
    def identify(self, environ):
        """
        Override the parent's identifier to introduce a login counter
        (possibly along with a post-login page) and load the login counter into
        the ``environ``.
        
        """
        
        identity = super(FriendlyRedirectingFormPlugin, self).identify(environ)
        
        if environ['PATH_INFO'] == self.login_handler_path:
            ## We are on the URL where repoze.who processes authentication. ##
            # Let's append the login counter to the query string of the
            # "came_from" URL. It will be used by the challenge below if
            # authorization is denied for this request.
            destination = environ['repoze.who.application'].location()
            if self.post_login_url:
                # There's a post-login page, so we have to replace the
                # destination with it.
                destination = self._get_full_path(self.post_login_url,
                                                  environ)
                # Let's check if there's a referrer defined.
                query_parts = parse_dict_querystring(environ)
                if 'came_from' in query_parts:
                    # There's a referrer URL defined, so we have to pass it to
                    # the post-login page as a GET variable.
                    destination = self._insert_qs_variable(
                        destination,
                        'came_from',
                        query_parts['came_from'])
            failed_logins = self._get_logins(environ, True)
            new_dest = self._set_logins_in_url(destination, failed_logins)
            environ['repoze.who.application'] = HTTPFound(new_dest)
            
        elif environ['PATH_INFO'] == self.login_form_url or \
             self._get_logins(environ):
            ##  We are on the URL that displays the from OR any other page  ##
            ##   where the login counter is included in the query string.   ##
            # So let's load the counter into the environ and then hide it from
            # the query string (it will cause problems in frameworks like TG2,
            # where this unexpected variable would be passed to the controller)
            environ['repoze.who.logins'] = self._get_logins(environ, True)
            # Hiding the GET variable in the environ:
            qs = parse_dict_querystring(environ)
            if self.login_counter_name in qs:
                del qs[self.login_counter_name]
                environ['QUERY_STRING'] = urlencode(qs, doseq=True)
        
        return identity
    
    def challenge(self, environ, status, app_headers, forget_headers):
        """
        Override the parent's challenge to avoid challenging the user on
        logout, introduce a post-logout page and/or pass the login counter 
        to the login form.
        
        """
        
        challenger = super(FriendlyRedirectingFormPlugin, self).\
                     challenge(environ, status, app_headers, forget_headers)
        
        headers = [(h, v) for (h, v) in challenger.headers
                   if h.lower() != 'location']
        
        if environ['PATH_INFO'] == self.logout_handler_path:
            # Let's log the user out without challenging.
            came_from = environ.get('came_from')
            script_path = environ.get('SCRIPT_PATH', '')
            if self.post_logout_url:
                # Redirect to a predefined "post logout" URL.
                destination = self._get_full_path(self.post_logout_url,
                                                  environ)
                if came_from:
                    destination = self._insert_qs_variable(
                                  destination, 'came_from', came_from)
            else:
                # Redirect to the referrer URL.
                destination = came_from or script_path or '/'
            return HTTPFound(destination, headers=headers)
        
        if 'repoze.who.logins' in environ:
            # Login failed! Let's redirect to the login form and include
            # the login counter in the query string
            environ['repoze.who.logins'] += 1
            #raise Exception(environ['repoze.who.logins'])
            # Re-building the URL:
            old_destination = challenger.location()
            destination = self._set_logins_in_url(old_destination,
                                                  environ['repoze.who.logins'])
            return HTTPFound(destination, headers=headers)
        
        return challenger
    
    def _get_full_path(self, path, environ):
        """
        Return the full path to ``path`` by prepending the SCRIPT_PATH.
        
        If ``path`` is a URL, do nothing.
        
        """
        if path.startswith('/'):
            path = environ.get('SCRIPT_PATH', '') + path
        return path
    
    def _get_logins(self, environ, force_typecast=False):
        """
        Return the login counter from the query string in the ``environ``.
        
        If it's not possible to convert it into an integer and  
        ``force_typecast`` is ``True``, it will be set to zero (int(0)). 
        Otherwise, it will be ``None`` or an string.
        
        """
        variables = parse_dict_querystring(environ)
        failed_logins = variables.get(self.login_counter_name)
        if force_typecast:
            try:
                failed_logins = int(failed_logins)
            except (ValueError, TypeError):
                failed_logins = 0
        return failed_logins
    
    def _set_logins_in_url(self, url, logins):
        """
        Insert the login counter variable with the ``logins`` value into
        ``url`` and return the new URL.
        
        """
        return self._insert_qs_variable(url, self.login_counter_name, logins)
    
    def _insert_qs_variable(self, url, var_name, var_value):
        """
        Insert the variable ``var_name`` with value ``var_value`` in the query
        string of ``url`` and return the new URL.
        
        """
        url_parts = list(urlparse(url))
        query_parts = parse_qs(url_parts[4])
        query_parts[var_name] = var_value
        url_parts[4] = urlencode(query_parts, doseq=True)
        return urlunparse(url_parts)


#{ The Quickstart itself


def find_plugin_translations(translations={}):
    """
    Process global translations for :mod:`repoze.who`/:mod:`repoze.what`
    SQLAlchemy plugins.
    
    These "translations" are usually defined in quickstarted projects, in
    {tg2_project}.config.app_cfg.base_config.sa_auth.translations
    
    :param translations: The translation dictionary.
    :type translations: dict
    :return: The respective translations for the group and permission adapters,
        the authenticator and the MD provider.
    :rtype: dict
    
    """
    
    group_adapter = {}
    permission_adapter = {}
    authenticator = {}
    mdprovider = {}
    
    if 'validate_password' in translations:
        authenticator['validate_password'] = translations['validate_password']
    if 'user_name' in translations:
        group_adapter['item_name'] = translations['user_name']
        authenticator['user_name'] = translations['user_name']
        mdprovider['user_name'] = translations['user_name']
    if 'users' in translations:
        group_adapter['items'] = translations['users']
    if 'group_name' in translations:
        group_adapter['section_name'] = translations['group_name']
        permission_adapter['item_name'] = translations['group_name']
    if 'groups' in translations:
        group_adapter['sections'] = translations['groups']
        permission_adapter['items'] = translations['groups']
    if 'permission_name' in translations:
        permission_adapter['section_name'] = translations['permission_name']
    if 'permissions' in translations:
        permission_adapter['sections'] = translations['permissions']
        
    final_translations = {
        'group_adapter': group_adapter,
        'permission_adapter': permission_adapter,
        'authenticator': authenticator,
        'mdprovider': mdprovider}
    return final_translations


def setup_sql_auth(app, user_class, group_class, permission_class,
                   dbsession, form_plugin=None, form_identifies=True,
                   cookie_secret='secret', cookie_name='authtkt',
                   login_url='/login', login_handler='/login_handler',
                   post_login_url=None, logout_handler='/logout_handler',
                   post_logout_url=None, login_counter_name=None,
                   translations={}, **who_args):
    """
    Configure :mod:`repoze.who` and :mod:`repoze.what` with SQL-only 
    authentication and authorization, respectively.
    
    :param app: Your WSGI application.
    :param user_class: The SQLAlchemy/Elixir class for the users.
    :param group_class: The SQLAlchemy/Elixir class for the groups.
    :param permission_class: The SQLAlchemy/Elixir class for the permissions.
    :param dbsession: The SQLAlchemy/Elixir session.
    :param form_plugin: The main :mod:`repoze.who` challenger plugin; this is 
        usually a login form.
    :param form_identifies: Whether the ``form_plugin`` may and should act as
        an :mod:`repoze.who` identifier.
    :type form_identifies: bool
    :param cookie_secret: The "secret" for the AuthTktCookiePlugin.
    :type cookie_secret: str
    :param cookie_name: The name for the AuthTktCookiePlugin.
    :type cookie_name: str
    :param login_url: The URL where the login form is displayed.
    :type login_url: str
    :param login_handler: The URL where the login form is submitted.
    :type login_handler: str
    :param post_login_url: The URL/path where users should be redirected to
        after login.
    :type post_login_url: str
    :param logout_handler: The URL where the logout is handled.
    :type login_handler: str
    :param post_logout_url: The URL/path where users should be redirected to
        after logout.
    :type post_logout_url: str
    :param login_counter_name: The name of the variable in the query string
        that represents the login counter; defaults to ``__logins``.
    :type login_counter_name: str
    :param translations: The model translations.
    :type translations: dict
    :return: The WSGI application with authentication and authorization
        middleware.
    
    It configures :mod:`repoze.who` with the following plugins:
    
    * Identifiers:
    
      * :class:`FriendlyRedirectingFormPlugin` as the first identifier and 
        challenger -- using ``login`` as the URL/path where the login form will
        be displayed, ``login_handler`` as the URL/path where the form will be 
        sent and ``logout_handler`` as the URL/path where the user will be 
        logged out. The so-called *rememberer* of such an identifier will be 
        the identifier below.
        
        If ``post_login_url`` is defined, the user will be redirected to that
        page after login. Likewise, if ``post_logout_url`` is defined, the
        user will be redirected to that page after logout.
        
        You can override the :class:`FriendlyRedirectingFormPlugin`'s login 
        counter variable name (which defaults to ``__logins``) by defining
        ``login_counter_name``.
        
        .. tip::
        
            This plugin may be overridden with the ``form_plugin`` argument. 
            See also the ``form_identifies`` argument.
      * :class:`repoze.who.plugins.auth_tkt.AuthTktCookiePlugin`. You can
        customize the cookie name and secret using the ``cookie_name`` and
        ``cookie_secret`` arguments, respectively.
      
      Then it will append the identifiers you pass through the ``identifiers``
      keyword argument, if any.
    
    * Authenticators:
    
      * :class:`repoze.who.plugins.sa.SQLAlchemyAuthenticatorPlugin`, using
        the ``user_class`` and ``dbsession`` arguments as its user class and
        DB session, respectively.
      
      Then it will append the authenticators you pass through the 
      ``authenticators`` keyword argument, if any.
    
    * Challengers:
    
      * The same Form-based plugin used in the identifiers.
      
      Then it will append the challengers you pass through the 
      ``challengers`` keyword argument, if any.
    
    * Metadata providers:
    
      * :class:`repoze.who.plugins.sa.SQLAlchemyUserMDPlugin`, using
        the ``user_class`` and ``dbsession`` arguments as its user class and
        DB session, respectively.
      
      Then it will append the metadata providers you pass through the 
      ``mdproviders`` keyword argument, if any.
    
    Additional keyword arguments will be passed to 
    :class:`repoze.who.middleware.PluggableAuthenticationMiddleware`.
    
    """
    plugin_translations = find_plugin_translations(translations)
    
    source_adapters = configure_sql_adapters(
        user_class,
        group_class,
        permission_class,
        dbsession,
        plugin_translations['group_adapter'],
        plugin_translations['permission_adapter']
        )
    group_adapters = {'sql_auth': source_adapters['group']}
    permission_adapters = {'sql_auth': source_adapters['permission']}
    
    # Setting the repoze.who authenticators:
    sqlauth = SQLAlchemyAuthenticatorPlugin(user_class, dbsession)
    sqlauth.translations.update(plugin_translations['authenticator'])
    if 'authenticators' not in who_args:
        who_args['authenticators'] = []
    who_args['authenticators'].append(('sqlauth', sqlauth))
    
    cookie = AuthTktCookiePlugin(cookie_secret, cookie_name)
    
    # Setting the repoze.who identifiers
    if 'identifiers' not in who_args:
        who_args['identifiers'] = []
    who_args['identifiers'].append(('cookie', cookie))
    
    if form_plugin is None:
        form = FriendlyRedirectingFormPlugin(
            login_url,
            login_handler,
            logout_handler,
            post_login_url=post_login_url,
            post_logout_url=post_logout_url,
            login_counter_name=login_counter_name,
            rememberer_name='cookie')
    else:
        form = form_plugin
    
    if form_identifies:
        who_args['identifiers'].insert(0, ('main_identifier', form))
    
    # Setting the repoze.who challengers:
    if 'challengers' not in who_args:
        who_args['challengers'] = []
    who_args['challengers'].append(('form', form))
    
    # Setting up the repoze.who mdproviders:
    sql_user_md = SQLAlchemyUserMDPlugin(user_class, dbsession)
    sql_user_md.translations.update(plugin_translations['mdprovider'])
    if 'mdproviders' not in who_args:
        who_args['mdproviders'] = []
    who_args['mdproviders'].append(('sql_user_md', sql_user_md))
    
    middleware = setup_auth(app, group_adapters, permission_adapters, 
                            **who_args)
    return middleware


#}
