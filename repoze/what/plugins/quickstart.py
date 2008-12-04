# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007, Agendaless Consulting and Contributors.
# Copyright (c) 2008, Florent Aide <florent.aide@gmail.com> and
#                     Gustavo Narea <me@gustavonarea.net>
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

"""Sample plugins and middleware configuration for repoze.what."""

from zope.interface import implements
from repoze.who.interfaces import IAuthenticator
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from repoze.what.middleware import setup_auth
from repoze.what.plugins.sql import configure_sql_adapters

class SQLAuthenticatorPlugin(object):
    implements(IAuthenticator)
    
    def __init__(self, user_class, dbsession):
        self.user_class = user_class
        self.dbsession = dbsession
        self.translations = {
            'user_name': 'user_name',
            'validate_password': 'validate_password'
        }

    # IAuthenticator
    def authenticate(self, environ, identity):
        if not 'login' in identity:
            return None
        
        query = self.dbsession.query(self.user_class)
        query = query.filter(self.user_class.user_name==identity['login'])
        try:
            user = query.one()
            if user.validate_password(identity['password']):
                return user.user_name
        except (NoResultFound, MultipleResultsFound):
            # As recommended in the docs for repoze.who, it's important to
            # verify that there's only one matching userid.
            return


def find_plugin_translations(translations={}):
    """
    Process translations defined in TG2 quickstarted projects.
    
    These "translations" are usually defined in quickstarted projects, in
    {tg2_project}.config.app_cfg.base_config.sa_auth.translations
    
    @param translations: The TG2 applications' base_config.sa_auth.translations
    @return: The respective translations for the group and permission adapters
        and the authenticator.
    @rtype: C{dict}
    
    """
    
    group_adapter = {}
    permission_adapter = {}
    authenticator = {}
    
    if 'validate_password' in translations:
        authenticator['validate_password'] = translations['validate_password']
    if 'user_name' in translations:
        group_adapter['item_name'] = translations['user_name']
        authenticator['user_name'] = translations['user_name']
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
        'authenticator': authenticator}
    return final_translations


def setup_sql_auth(app, user_class, group_class, permission_class,
                   dbsession, form_plugin=None, form_identifies=True,
                   cookie_secret='secret', cookie_name='authtkt',
                   translations={}, **who_args):
    """
    A basic configuration of repoze.who and repoze.what with SQL-only
    authentication/authorization.
    
    Additional keyword arguments will be passed to repoze.who's
    PluggableAuthenticationMiddleware.
    
    @param app: The WSGI application object.
    @param user_class: The SQLAlchemy class for the users.
    @param group_class: The SQLAlchemy class for the groups.
    @param permission_class: The SQLAlchemy class for the permissions.
    @param dbsession: The SQLAlchemy session.
    @param form_plugin: The main repoze.who IChallenger; this is usually a
        login form.
    @param form_identifies: Whether the C{form_plugin} may and should act as
        an repoze.who identifier.
    @param cookie_secret: The "secret" for the AuthTktCookiePlugin.
    @param cookie_name: The name for the AuthTktCookiePlugin.
    @param translations: The translation dictionary for the model.
    @return: The WSGI application with authentication and authorization.
    
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
    sqlauth = SQLAuthenticatorPlugin(user_class, dbsession)
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
        form = RedirectingFormPlugin('/login', '/login_handler',
                                     '/logout_handler',
                                     rememberer_name='cookie')
    else:
        form = form_plugin
    
    if form_identifies:
        who_args['identifiers'].insert(0, ('main_identifier', form))
    
    # Setting the repoze.who challengers:
    if 'challengers' not in who_args:
        who_args['challengers'] = []
    who_args['challengers'].append(('form', form))
    
    middleware = setup_auth(app, group_adapters, permission_adapters, 
                            **who_args)
    return middleware
