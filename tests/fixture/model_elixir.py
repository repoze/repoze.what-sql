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

import md5
import sha
from datetime import datetime

from sqlalchemy.orm import scoped_session, sessionmaker
import elixir
from elixir import Entity, Field
from elixir import DateTime, Unicode
from elixir import using_options
from elixir import ManyToMany

from tg import config

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

    def __repr__(self):
        return '<User: email="%s", display name="%s">' % (
                self.email_address, self.display_name)



    @property
    def permissions(self):
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms

    @classmethod
    def by_email_address(cls, email):
        """A class method that can be used to search users
        based on their email addresses since it is unique.
        """
        return DBSession.query(cls).filter(cls.email_address==email).first()

    @classmethod
    def by_user_name(cls, username):
        """A class method that permits to search users
        based on their user_name attribute.
        """
        return DBSession.query(cls).filter(cls.user_name==username).first()


    def _set_password(self, password):
        """encrypts password on the fly using the encryption
        algo defined in the configuration
        """
        algorithm = self.get_encryption_method()
        self._password = self.__encrypt_password(algorithm, password)

    def _get_password(self):
        """returns password
        """
        return self._password

    password = descriptor=property(_get_password, _set_password)

    def __encrypt_password(self, algorithm, password):
        """Hash the given password with the specified algorithm. Valid values
        for algorithm are 'md5' and 'sha1'. All other algorithm values will
        be essentially a no-op."""
        hashed_password = password

        if isinstance(password, unicode):
            password_8bit = password.encode('UTF-8')

        else:
            password_8bit = password

        if "md5" == algorithm:
            hashed_password = md5.new(password_8bit).hexdigest()

        elif "sha1" == algorithm:
            hashed_password = sha.new(password_8bit).hexdigest()

        # TODO: re-add the possibility to provide own hasing algo
        # here... just get the real config...

        #elif "custom" == algorithm:
        #    custom_encryption_path = turbogears.config.get(
        #        "auth.custom_encryption", None )
        #
        #    if custom_encryption_path:
        #        custom_encryption = turbogears.util.load_class(
        #            custom_encryption_path)

        #    if custom_encryption:
        #        hashed_password = custom_encryption(password_8bit)

        # make sure the hased password is an UTF-8 object at the end of the
        # process because SQLAlchemy _wants_ a unicode object for Unicode columns
        if not isinstance(hashed_password, unicode):
            hashed_password = hashed_password.decode('UTF-8')

        return hashed_password

    def get_encryption_method(self):
        """returns the encryption method from the config
        If None is set, or auth is disabled this will return None
        """
        auth_system = config.get('sa_auth', None)
        if auth_system is None:
            # if auth is not activated in the config we should warn
            # the admin through the logs... and return None
            return None

        return auth_system.get('password_encryption_method', None)

    def validate_password(self, password):
        """Check the password against existing credentials.
        this method _MUST_ return a boolean.

        @param password: the password that was provided by the user to
        try and authenticate. This is the clear text version that we will
        need to match against the (possibly) encrypted one in the database.
        @type password: unicode object
        """
        algorithm = self.get_encryption_method()
        return self.password == self.__encrypt_password(algorithm, password)


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
