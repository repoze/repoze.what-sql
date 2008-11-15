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
SQL plugin for repoze.what based on SQLAlchemy.

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

from repoze.what.adapters import BaseSourceAdapter, SourceError

__all__ = ['SqlGroupsAdapter', 'SqlPermissionsAdapter',
           'configure_sql_adapters']


class _BaseSqlAdapter(BaseSourceAdapter):
    """Base class for SQL source adapters."""

    def __init__(self, parent_class, children_class, session):
        """
        Create an SQL source adapter.

        @param parent_class: The SQLAlchemy table of the section.
        @param children_class: The SQLAlchemy table of the items.
        @param session: The SQLAlchemy session.

        """
        super(_BaseSqlAdapter, self).__init__()
        self.session = session
        self.parent_class = parent_class
        self.children_class = children_class

    # BaseSourceAdapter
    def _get_all_sections(self):
        sections = {}
        sections_as_rows = self.session.query(self.parent_class).all()
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

    # BaseSourceAdapter
    def _find_sections(self, hint):
        raise NotImplementedError('This is implemented in the groups and '
                                  'permissions adapters.')

    # TODO: Factor out the common code in _include_items and _exclude_items

    # BaseSourceAdapter
    def _include_items(self, section, items):
        self.session.begin(subtransactions=True)
        item, included_items = self._get_items_as_rowset(section)
        try:
            for item_to_include in items:
                item_as_row = self._get_item_as_row(item_to_include)
                included_items.append(item_as_row)
            self.session.commit()
        except SQLAlchemyError, msg:
            self.session.rollback()
            raise SourceError(msg)

    # BaseSourceAdapter
    def _exclude_items(self, section, items):
        self.session.begin(subtransactions=True)
        item, included_items = self._get_items_as_rowset(section)
        try:
            for item_to_exclude in items:
                item_as_row = self._get_item_as_row(item_to_exclude)
                included_items.remove(item_as_row)
            self.session.commit()
        except SQLAlchemyError, msg:
            self.session.rollback()
            raise SourceError(msg)

    # BaseSourceAdapter
    def _item_is_included(self, section, item):
        return item in self._get_section_items(section)

    # BaseSourceAdapter
    def _create_section(self, section):
        self.session.begin(subtransactions=True)
        section_as_row = self.parent_class()
        # Creating the section with an empty set of items:
        setattr(section_as_row, self.translations['section_name'], section)
        setattr(section_as_row, self.translations['items'], [])
        try:
            self.session.add(section_as_row)
            self.session.commit()
        except SQLAlchemyError, msg:
            self.session.rollback()
            raise SourceError(msg)

    # BaseSourceAdapter
    def _edit_section(self, section, new_section):
        self.session.begin(subtransactions=True)
        section_as_row = self._get_section_as_row(section)
        setattr(section_as_row, self.translations['section_name'], new_section)
        try:
            self.session.commit()
        except SQLAlchemyError, msg:
            self.session.rollback()
            raise SourceError(msg)

    # BaseSourceAdapter
    def _delete_section(self, section):
        self.session.begin(subtransactions=True)
        section_as_row = self._get_section_as_row(section)
        try:
            self.session.delete(section_as_row)
            self.session.commit()
        except SQLAlchemyError, msg:
            self.session.rollback()
            raise SourceError(msg)

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
        Return the SQLAlchemy row for the section called C{section_name}.

        When dealing with a group source, the section is a group. And when
        dealing with a permission source, the section is a permission.

        """
        # "field" usually equals to {tg_package}.model.Group.group_name
        # or {tg_package}.model.Permission.permission_name
        field = getattr(self.parent_class, self.translations['section_name'])
        query = self.session.query(self.parent_class)
        try:
            section_as_row = query.filter(field==section_name).one()
        except NoResultFound:
            msg = 'Section (%s) "%s" is not defined in the parent table'
            msg = msg % (self.translations['section_name'], section_name)
            raise SourceError(msg)
        return section_as_row

    def _get_item_as_row(self, item_name):
        """
        Return the SQLAlchemy row for the item called C{item_name}.

        When dealing with a group source, the item is a user. And when dealing
        with a permission source, the item is a group.

        """
        # "field" usually equals to {tg_package}.model.User.user_name
        # or {tg_package}.model.Group.group_name
        field = getattr(self.children_class, self.translations['item_name'])
        query = self.session.query(self.children_class)
        try:
            item_as_row = query.filter(field==item_name).one()
        except NoResultFound:
            msg = 'Item (%s) "%s" does not exist in the child table'
            msg = msg % (self.translations['item_name'], item_name)
            raise SourceError(msg)
        return item_as_row

    def _get_items_as_rowset(self, section_name):
        """
        Return the items of the section called C{section_name}.

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
    """The SQL group source adapter."""

    def __init__(self, *args):
        super(SqlGroupsAdapter, self).__init__(*args)
        self.translations = {
            'section_name': 'group_name',
            'sections': 'groups',
            'item_name': 'user_name',
            'items': 'users'
        }

    def _find_sections(self, identity):
        id_ = identity['repoze.who.userid']
        try:
            user = self._get_item_as_row(id_)
        except SourceError:
            return set()

        # Also load the user object into the identity
        identity['user'] = user

        user_memberships = getattr(user, self.translations['sections'])
        return set([group.group_name for group in user_memberships])


class SqlPermissionsAdapter(_BaseSqlAdapter):
    """The SQL permission source adapter."""

    def __init__(self, *args):
        super(SqlPermissionsAdapter, self).__init__(*args)
        self.translations = {
            'section_name': 'permission_name',
            'sections': 'permissions',
            'item_name': 'group_name',
            'items': 'groups'
        }

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
    Configure and return group and permission adapters that share the
    same model.

    You may want to use the C{find_plugin_translations()} function provided
    by the quickstart utilities to format the values of C{group_translations}
    and C{permission_translations}.

    @param user_class: The SQLAlchemy class for the users.
    @param group_class: The SQLAlchemy class for the groups.
    @param permission_class: The SQLAlchemy class for the permissions.
    @param session: The SQLAlchemy session.
    @param group_translations: The translations for the group adapter.
    @type group_translations: C{dict}
    @param permission_translations: The translations for the permission adapter.
    @type permission_translations: C{dict}

    """
    # Creating the adapters:
    group = SqlGroupsAdapter(group_class, user_class, session)
    permission = SqlPermissionsAdapter(permission_class, group_class, session)
    # Translating some fields:
    group.translations.update(group_translations)
    permission.translations.update(permission_translations)

    return {'group': group, 'permission': permission}


#}
