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

"""Test suite for the SQL plugin."""

import unittest

from repoze.what.plugins.quickstart import SQLAuthenticatorPlugin
from repoze.what.plugins.sql import SqlGroupsAdapter, \
                                            SqlPermissionsAdapter, \
                                            configure_sql_adapters
from repoze.what.adapters.testutil import GroupsAdapterTester, \
                                                  PermissionsAdapterTester

import databasesetup
from model import User, Group, Permission, DBSession


class _BaseSqlAdapterTester(unittest.TestCase):
    """Base class for the test suite of the SQL source adapters"""
    
    def tearDown(self):
        databasesetup.teardownDatabase()


class TestSqlGroupsAdapter(GroupsAdapterTester, _BaseSqlAdapterTester):
    """Test suite for the SQL group source adapter"""
    
    def setUp(self):
        super(TestSqlGroupsAdapter, self).setUp()
        databasesetup.setup_database()
        self.adapter = SqlGroupsAdapter(databasesetup.Group,
                                        databasesetup.User,
                                        databasesetup.DBSession)


class TestSqlPermissionsAdapter(PermissionsAdapterTester,
                                _BaseSqlAdapterTester):
    """Test suite for the SQL permission source adapter"""
    
    def setUp(self):
        super(TestSqlPermissionsAdapter, self).setUp()
        databasesetup.setup_database()
        self.adapter = SqlPermissionsAdapter(databasesetup.Permission,
                                             databasesetup.Group,
                                             databasesetup.DBSession)


class TestAdaptersConfigurator(unittest.TestCase):
    """Tests for the L{configure_sql_adapters} utility"""
    
    def test_without_translations(self):
        adapters = configure_sql_adapters(User, Group, Permission, DBSession)
        group_adapter = adapters['group']
        permission_adapter = adapters['permission']
        assert isinstance(group_adapter, SqlGroupsAdapter)
        assert isinstance(permission_adapter, SqlPermissionsAdapter)
        self.assertEquals(DBSession, group_adapter.dbsession,
                          permission_adapter.dbsession)
        self.assertEqual(User, group_adapter.children_class)
        self.assertEquals(Group, group_adapter.parent_class,
                          permission_adapter.children_class)
        self.assertEqual(Permission, permission_adapter.parent_class)
    
    def test_with_translations(self):
        group_translations = {
            'item_name': 'member_name',
            'items': 'members'}
        permission_translations = {
            'section_name': 'authorization_name',
            'sections': 'authorizations'}
        adapters = configure_sql_adapters(User, Group, Permission, DBSession,
                                          group_translations,
                                          permission_translations)
        group_adapter = adapters['group']
        permission_adapter = adapters['permission']
        # The verifications...
        self.assertEqual(group_adapter.translations['item_name'],
                         group_translations['item_name'])
        self.assertEqual(group_adapter.translations['items'],
                         group_translations['items'])
        self.assertEqual(permission_adapter.translations['section_name'],
                         permission_translations['section_name'])
        self.assertEqual(permission_adapter.translations['sections'],
                         permission_translations['sections'])
        # Checking that the default translation is used when not overriden:
        self.assertEquals(group_adapter.translations['section_name'],
                          permission_adapter.translations['item_name'],
                          'group_name')
