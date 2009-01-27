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

"""Sample plugins and middleware configuration for repoze.what."""

from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
from repoze.who.plugins.sa import SQLAlchemyAuthenticatorPlugin, \
                                  SQLAlchemyUserMDPlugin

from repoze.what.middleware import setup_auth
from repoze.what.plugins.sql import configure_sql_adapters


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
                   logout_handler='/logout_handler', translations={}, 
                   **who_args):
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
    :param logout_handler: The URL where the logout is handled.
    :type login_handler: str
    :param translations: The model translations.
    :return: The WSGI application with authentication and authorization
        middleware.
    
    It configures :mod:`repoze.who` with the following plugins:
    
    * Identifiers:
    
      * :class:`repoze.who.plugins.auth_tkt.AuthTktCookiePlugin`. You can
        customize the cookie name and secret using the ``cookie_name`` and
        ``cookie_secret`` arguments, respectively.
      * :class:`repoze.who.plugins.form.RedirectingFormPlugin` as the first
        identifier and challenger -- using ``login`` as the relative URL that 
        will display the login form, ``login_handler`` as the relative URL 
        where the form will be sent and ``logout_handler`` as the relative URL
        where the user will be logged out. The so-called *rememberer* of such 
        identifier will be an instance of 
        :class:`repoze.who.plugins.auth_tkt.AuthTktCookiePlugin`.
        
        .. tip::
        
            This plugin may be overriden with the ``form_plugin`` argument. See
            also the ``form_identifies`` argument.
      
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
        from repoze.who.plugins.form import RedirectingFormPlugin
        form = RedirectingFormPlugin(login_url, login_handler,
                                     logout_handler, rememberer_name='cookie')
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
