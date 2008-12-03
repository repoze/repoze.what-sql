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

"""Mock Elixir-powered model definition."""

from hashlib import sha1
from datetime import datetime

from sqlalchemy.orm import scoped_session, sessionmaker
import elixir
from elixir import Entity, Field
from elixir import DateTime, Unicode
from elixir import using_options
from elixir import ManyToMany

DBSession = scoped_session(sessionmaker(autoflush=True, autocommit=False))

metadata = elixir.metadata
elixir.session = DBSession

def init_model(engine):
    """Call me before using any of the tables or classes in the model."""
    DBSession.configure(bind=engine)
    metadata.bind = engine


class User(Entity):
    """Reasonably basic User definition. Probably would want additional
    attributes.
    """
    using_options(tablename="tg_user", auto_primarykey="user_id")

    user_name = Field(Unicode(16), required=True, unique=True)

    email_address = Field(Unicode(255), required=True, unique=True)

    display_name = Field(Unicode(255))

    created = Field(DateTime, default=datetime.now)

    _password = Field(Unicode(40), colname="password", required=True)

    groups = ManyToMany(
        "Group",
        inverse="users",
        tablename="tg_user_group",
        local_colname="group_id",
        remote_colname="user_id",
        )

    def _set_password(self, password):
        """encrypts password on the fly"""
        self._password = self.__encrypt_password(password)

    def _get_password(self):
        """returns password"""
        return self._password

    password = descriptor=property(_get_password, _set_password)

    def __encrypt_password(self, password):
        """Hash the given password with SHA1."""
        
        if isinstance(password, unicode):
            password_8bit = password.encode('UTF-8')

        else:
            password_8bit = password

        hashed_password = sha1()
        hashed_password.update(password_8bit)
        hashed_password = hashed_password.hexdigest()

        # make sure the hased password is an UTF-8 object at the end of the
        # process because SQLAlchemy _wants_ a unicode object for Unicode columns
        if not isinstance(hashed_password, unicode):
            hashed_password = hashed_password.decode('UTF-8')

        return hashed_password

    def validate_password(self, password):
        """Check the password against existing credentials.
        this method _MUST_ return a boolean.

        @param password: the password that was provided by the user to
        try and authenticate. This is the clear text version that we will
        need to match against the (possibly) encrypted one in the database.
        @type password: unicode object
        """
        return self.password == self.__encrypt_password(password)


class Group(Entity):
    """An ultra-simple group definition.
    """
    using_options(tablename="tg_group", auto_primarykey="group_id")

    group_name = Field(Unicode(16), unique=True)

    display_name = Field(Unicode(255))

    created = Field(DateTime, default=datetime.now)

    users = ManyToMany("User")

    permissions = ManyToMany(
        "Permission",
        inverse="groups",
        tablename="tg_group_permission",
        local_colname="group_id",
        remote_colname="permission_id",
        )

    def __repr__(self):
        return '<Group: name=%s>' % self.group_name


class Permission(Entity):
    """A relationship that determines what each Group can do
    """
    using_options(tablename="tg_permission", auto_primarykey="permission_id")

    permission_name = Field(Unicode(16), unique=True)

    description = Field(Unicode(255))

    groups = ManyToMany("Group")
