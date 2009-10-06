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
SQL plugin for :mod:`repoze.what` based on SQLAlchemy.

This is a core plugin that provides ``source adapters`` for groups and
permissions stored in databases.

Below is the "translation" of the terminology used by repoze.what into
databases' terminology:
 * source -> database
 * section -> parent row (in a one-to-many relationship)
 * item -> a child row (in a one-to-many relationship)

In a group source adapter, a ``section`` is a group in the source (a parent
row) and its items are the users that belong to that section (its children
rows). In a permission source adapter, a ``section`` is a permission in the
source (a parent row) and its items are the groups that are granted that
permission (its children rows).

For developers to be able to use the names they want in their model, both the
groups and permissions source adapters use a "translation table" for the
field and table names involved:
  * Group source adapter:
    * "section_name" (default: "group_name"): The name of the table field that
      contains the primary key in the groups table.
    * "sections" (default: "groups"): The groups to which a given user belongs.
    * "item_name" (default: "user_name"): The name of the table field that
      contains the primary key in the users table.
    * "items" (default: "users"): The users that belong to a given group.
  * Permission source adapter:
    * "section_name" (default: "permission_name"): The name of the table field
      that contains the primary key in the permissions table.
    * "sections" (default: "permissions"): The permissions granted to a given
      group.
    * "item_name" (default: "group_name"): The name of the table field that
      contains the primary key in the groups table.
    * "items" (default: "groups"): The groups that are granted a given
      permission.

@attention: These adapters have a serious limitation, since they are based on
    one-to-many relations: If you're using the groups adapter, then your users'
    data must also be handled by SQLAlchemy; likewise, If you're using the
    permissions adapter, then your groups must also be handled by SQLAlchemy.
@attention: When using the SQL group adapter, it will load the authenticated
    used object into repoze.who's identity dict (under the "user" key).

"""

from sqlalchemy.exceptions import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import eagerload

from repoze.what.adapters import BaseSourceAdapter, SourceError

__all__ = ['SqlGroupsAdapter', 'SqlPermissionsAdapter',
           'configure_sql_adapters']


class _BaseSqlAdapter(BaseSourceAdapter):
    """Base class for SQL source adapters."""

    def __init__(self, parent_class, children_class, dbsession):
        """
        Create an SQL source adapter.

        :param parent_class: The SQLAlchemy table of the section.
        :param children_class: The SQLAlchemy table of the items.
        :param dbsession: The SQLAlchemy session.

        """
        super(_BaseSqlAdapter, self).__init__()
        self.dbsession = dbsession
        self.parent_class = parent_class
        self.children_class = children_class

    # BaseSourceAdapter
    def _get_all_sections(self):
        sections = {}
        sections_as_rows = self.dbsession.query(self.parent_class).all()
        for section_as_row in sections_as_rows:
            section_name = getattr(section_as_row,
                                   self.translations['section_name'])
            sections[section_name] = self._get_section_items(section_name)
        return sections

    # BaseSourceAdapter
    def _get_section_items(self, section):
        section_as_row = self._get_section_as_row(section)
        # A short-cut a translation:
        item_name = self.translations['item_name']
        # The name of all the items that belong to the section in question:
        items_as_rowset = getattr(section_as_row, self.translations['items'])
        return set((getattr(i, item_name) for i in items_as_rowset))

    # TODO: Factor out the common code in _include_items and _exclude_items

    # BaseSourceAdapter
    def _include_items(self, section, items):
        self.dbsession.begin(subtransactions=True)
        item, included_items = self._get_items_as_rowset(section)
        for item_to_include in items:
            item_as_row = self._get_item_as_row(item_to_include)
            included_items.append(item_as_row)
        self.dbsession.commit()

    # BaseSourceAdapter
    def _exclude_items(self, section, items):
        self.dbsession.begin(subtransactions=True)
        item, included_items = self._get_items_as_rowset(section)
        for item_to_exclude in items:
            item_as_row = self._get_item_as_row(item_to_exclude)
            included_items.remove(item_as_row)
        self.dbsession.commit()

    # BaseSourceAdapter
    def _item_is_included(self, section, item):
        return item in self._get_section_items(section)

    # BaseSourceAdapter
    def _create_section(self, section):
        self.dbsession.begin(subtransactions=True)
        section_as_row = self.parent_class()
        # Creating the section with an empty set of items:
        setattr(section_as_row, self.translations['section_name'], section)
        setattr(section_as_row, self.translations['items'], [])
        self.dbsession.add(section_as_row)
        self.dbsession.commit()

    # BaseSourceAdapter
    def _edit_section(self, section, new_section):
        self.dbsession.begin(subtransactions=True)
        section_as_row = self._get_section_as_row(section)
        setattr(section_as_row, self.translations['section_name'], new_section)
        self.dbsession.commit()

    # BaseSourceAdapter
    def _delete_section(self, section):
        self.dbsession.begin(subtransactions=True)
        section_as_row = self._get_section_as_row(section)
        self.dbsession.delete(section_as_row)
        self.dbsession.commit()

    # BaseSourceAdapter
    def _section_exists(self, section):
        # TODO: There must be a more elegant way to do this with SQLAlchemy
        try:
            self._get_section_as_row(section)
            return True
        except SourceError:
            return False

    def _get_section_as_row(self, section_name):
        """
        Return the SQLAlchemy row for the section called ``section_name``.

        When dealing with a group source, the section is a group. And when
        dealing with a permission source, the section is a permission.

        """
        # "field" usually equals to {tg_package}.model.Group.group_name
        # or {tg_package}.model.Permission.permission_name
        field = getattr(self.parent_class, self.translations['section_name'])
        query = self.dbsession.query(self.parent_class)
        try:
            section_as_row = query.filter(field==section_name).one()
        except NoResultFound:
            msg = 'Section (%s) "%s" is not defined in the parent table'
            msg = msg % (self.translations['section_name'], section_name)
            raise SourceError(msg)
        return section_as_row

    def _get_item_as_row(self, item_name):
        """
        Return the SQLAlchemy row for the item called ``item_name``.

        When dealing with a group source, the item is a user. And when dealing
        with a permission source, the item is a group.

        """
        # "field" usually equals to {tg_package}.model.User.user_name
        # or {tg_package}.model.Group.group_name
        field = getattr(self.children_class, self.translations['item_name'])
        query = self.dbsession.query(self.children_class).options(eagerload(self.translations['sections']))
        try:
            item_as_row = query.filter(field==item_name).one()
        except NoResultFound:
            msg = 'Item (%s) "%s" does not exist in the child table'
            msg = msg % (self.translations['item_name'], item_name)
            raise SourceError(msg)
        return item_as_row

    def _get_items_as_rowset(self, section_name):
        """
        Return the items of the section called ``section_name``.

        When dealing with a group source, the section is a group and the
        items (the result of this function) are the users that belong to such
        a group.

        When dealing with a permission source, the section is a permission and
        the items (the result of this function) are the groups that are granted
        such a permission.

        """
        section_as_row = self._get_section_as_row(section_name)
        items_as_rowset = getattr(section_as_row, self.translations['items'])
        return section_as_row, items_as_rowset


#{ Source adapters


class SqlGroupsAdapter(_BaseSqlAdapter):
    """
    The SQL group source adapter.
    
    To use this adapter, you must also define your users in a SQLAlchemy or
    Elixir-managed table with the relevant one-to-many (or many-to-many) 
    relationship defined with ``group_class``.
    
    On the other hand, unless stated otherwise, it will also assume the 
    following naming conventions in both classes; to replace any of those
    default values, you should use the ``translations`` dictionary of the
    relevant class accordingly:
    
    * In `group_class`, the attribute that contains the group name is 
      ``group_name`` (e.g., ``Group.group_name``).
    * In `group_class`, the attribute that contains the members of such a group
      is ``users`` (e.g., ``Group.users``).
    * In `user_class`, the attribute that contains the user's name is
      ``user_name`` (e.g., ``User.user_name``).
    * In `user_class`, the attribute that contains the groups to which a user
      belongs is ``groups`` (e.g., ``User.groups``).
    
    Example #1, without special naming conventions::
    
        # ...
        from repoze.what.plugins.sql import SqlGroupsAdapter
        from my_model import User, Group, DBSession
        
        groups = SqlGroupsAdapter(Group, User, DBSession)
        
        # ...
    
    Example #2, with special naming conventions::
    
        # ...
        from repoze.what.plugins.sql import SqlGroupsAdapter
        from my_model import Member, Team, DBSession
        
        groups = SqlGroupsAdapter(Team, Member, DBSession)
        
        # Replacing the default attributes, if necessary:
        
        # We have "Team.team_name" instead of "Team.group_name":
        groups.translations['section_name'] = 'team_name'
        # We have "Team.members" instead of "Team.users":
        groups.translations['items'] = 'members'
        # We have "Member.username" instead of "Member.user_name":
        groups.translations['item_name'] = 'username'
        # We have "Member.teams" instead of "Member.groups":
        groups.translations['sections'] = 'teams'
        
        # ...
    
    """

    def __init__(self, group_class, user_class, dbsession):
        """
        Create an SQL groups source adapter.
    
        :param group_class: The class that manages the groups.
        :param user_class: The class that manages the users.
        :param dbsession: The SQLALchemy/Elixir session to be used.
        
        """
        super(SqlGroupsAdapter, self).__init__(parent_class=group_class,
                                               children_class=user_class,
                                               dbsession=dbsession)
        self.translations = {
            'section_name': 'group_name',
            'sections': 'groups',
            'item_name': 'user_name',
            'items': 'users'
        }

    # BaseSourceAdapter
    def _find_sections(self, credentials):
        id_ = credentials['repoze.what.userid']
        user = credentials.get('repoze.what.userobj', None)
        if user is None:
            try:
                user = self._get_item_as_row(id_)
            except SourceError:
                return set()
            credentials['repoze.what.userobj'] = user

        return set([getattr(group, self.translations['section_name'])
                    for group in user.groups])


class SqlPermissionsAdapter(_BaseSqlAdapter):
    """
    The SQL permission source adapter.
    
    To use this adapter, you must also define your groups in a SQLAlchemy or
    Elixir-managed table with the relevant one-to-many (or many-to-many)
    relationship defined with ``permission_class``.
    
    On the other hand, unless stated otherwise, it will also assume the 
    following naming conventions in both classes; to replace any of those
    default values, you should use the ``translations`` dictionary of the
    relevant class accordingly:
    
    * In `permission_class`, the attribute that contains the permission name is 
      ``permission_name`` (e.g., ``Permission.permission_name``).
    * In `permission_class`, the attribute that contains the groups that are 
      granted such a permission is ``groups`` (e.g., ``Permission.groups``).
    * In `group_class`, the attribute that contains the group name is
      ``group_name`` (e.g., ``Group.group_name``).
    * In `group_class`, the attribute that contains the permissions granted to
      that group is ``permissions`` (e.g., ``Group.permissions``).
    
    Example #1, without special naming conventions::
    
        # ...
        from repoze.what.plugins.sql import SqlPermissionsAdapter
        from my_model import Group, Permission, DBSession
        
        groups = SqlPermissionsAdapter(Permission, Group, DBSession)
        
        # ...
    
    Example #2, with special naming conventions::
    
        # ...
        from repoze.what.plugins.sql import SqlPermissionsAdapter
        from my_model import Team, Permission, DBSession
        
        permissions = SqlPermissionsAdapter(Permission, Team, DBSession)
        
        # Replacing the default attributes, if necessary:
        
        # We have "Permission.perm_name" instead of "Permission.permission_name":
        permissions.translations['section_name'] = 'perm_name'
        # We have "Permission.teams" instead of "Permission.groups":
        permissions.translations['items'] = 'teams'
        # We have "Team.team_name" instead of "Team.group_name":
        permissions.translations['item_name'] = 'team_name'
        # We have "Team.perms" instead of "Team.permissions":
        permissions.translations['sections'] = 'perms'
        
        # ...
    
    
    """

    def __init__(self, permission_class, group_class, dbsession):
        """
        Create an SQL permissions source adapter.
        
        :param permission_class: The class that manages the permissions.
        :param group_class: The class that manages the groups.
        :param dbsession: The SQLALchemy/Elixir session to be used.
        
        """
        
        super(SqlPermissionsAdapter, self).__init__(
            parent_class=permission_class,
            children_class=group_class,
            dbsession=dbsession
            )
        self.translations = {
            'section_name': 'permission_name',
            'sections': 'permissions',
            'item_name': 'group_name',
            'items': 'groups'
        }

    # BaseSourceAdapter
    def _find_sections(self, group_name):
        try:
            group = self._get_item_as_row(group_name)
        except SourceError:
            return set()

        group_permissions = getattr(group, self.translations['sections'])

        return set([getattr(permission, self.translations['section_name'])
                    for permission in group_permissions])


#{ Utilities


def configure_sql_adapters(user_class, group_class, permission_class, session,
                           group_translations={}, permission_translations={}):
    """
    Configure and return group and permission adapters that share the same model.
    
    :param user_class: The class that manages the users.
    :param group_class: The class that manages the groups.
    :param user_class: The class that manages the permissions.
    :param dbsession: The SQLALchemy/Elixir session to be used.
    :param group_translations: The dictionary of translations for the group.
    :param permission_translations: The dictionary of translations for the permissions.
    :return: The ``group`` and ``permission`` adapters, configured.
    :rtype: dict 
    
    For this function to work, ``user_class`` and ``group_class`` must have the
    relevant one-to-many (or many-to-many) relationship; likewise, 
    ``group_class`` and ``permission_class`` must have the relevant one-to-many 
    (or many-to-many) relationship.
    
    Example::
    
        # ...
        from repoze.what.plugins.sql import configure_sql_adapters
        from my_model import User, Group, Permission, DBSession
        
        adapters = configure_sql_adapters(User, Group, Permission, DBSession)
        groups = adapters['group']
        permissions = adapters['permission']
        
        # ...

    """
    r = {}
    if group_class is not None:
        group = SqlGroupsAdapter(group_class, user_class, session)
        group.translations.update(group_translations)
        r['group'] = group
    if permission_class is not None:
        permission = SqlPermissionsAdapter(permission_class, group_class, session)
        permission.translations.update(permission_translations)
        r['permission'] = permission
    return r

#}
