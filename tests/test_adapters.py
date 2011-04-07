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

"""Test suite for the adapters provided by the  SQL plugin."""

import unittest

from repoze.what.plugins.sql import SqlGroupsAdapter, SqlPermissionsAdapter, \
                                    configure_sql_adapters
from repoze.what.adapters.testutil import GroupsAdapterTester, \
                                          PermissionsAdapterTester

import databasesetup
import databasesetup_translations
from fixture.model import User, Group, Permission, DBSession
from fixture.model_translations import Member, Team, Right, DBSession


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
        # The members of "nogroup" are determined dynamically via a property
        # on the user object:
        self.all_sections['nogroup'] = set()
    
    def test_property(self):
        """
        The attribute containing the groups may be a property instead of a
        relationship.
        
        """
        self.adapter.translations['sections'] = "fake_groups"
        
        groups = self.adapter.find_sections({'repoze.what.userid': "linus"})
        assert len(groups) == 1
        assert groups == set(["nogroup"])

class TestSqlPermissionsAdapter(PermissionsAdapterTester,
                                _BaseSqlAdapterTester):
    """Test suite for the SQL permission source adapter"""
    
    def setUp(self):
        super(TestSqlPermissionsAdapter, self).setUp()
        databasesetup.setup_database()
        self.adapter = SqlPermissionsAdapter(databasesetup.Permission,
                                             databasesetup.Group,
                                             databasesetup.DBSession)
        # The members of "nopermissions" are determined dynamically via a
        # property on the group object:
        self.all_sections['nopermission'] = set()
    
    def test_property(self):
        """
        The attribute containing the permissions may be a property instead of a
        relationship.
        
        """
        self.adapter.translations['sections'] = "fake_permissions"
        assert self.adapter.find_sections("trolls") == set(["nopermission"])


class TestSqlGroupsAdapterWithTranslations(GroupsAdapterTester,
                                           _BaseSqlAdapterTester):
    """Test suite for the SQL group source adapter with translations"""
    
    def setUp(self):
        super(TestSqlGroupsAdapterWithTranslations, self).setUp()
        databasesetup_translations.setup_database()
        self.adapter = SqlGroupsAdapter(
            Team,
            Member,
            databasesetup_translations.DBSession)
        translations = {
            'item_name': 'member_name',
            'items': 'members',
            'section_name': 'team_name',
            'sections': 'teams'}
        self.adapter.translations.update(translations)


class TestSqlPermissionsAdapterWithTranslations(PermissionsAdapterTester,
                                                _BaseSqlAdapterTester):
    """Test suite for the SQL permission source adapter with translations"""
    
    def setUp(self):
        super(TestSqlPermissionsAdapterWithTranslations, self).setUp()
        databasesetup_translations.setup_database()
        self.adapter = SqlPermissionsAdapter(
            Right,
            Team,
            databasesetup_translations.DBSession)
        translations = {
            'item_name': 'team_name',
            'items': 'teams',
            'section_name': 'right_name',
            'sections': 'rights'}
        self.adapter.translations.update(translations)


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
