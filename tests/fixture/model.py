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

"""Mock SQLAlchemy-powered model definition."""

import md5
import sha
from datetime import datetime

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import String, Unicode, UnicodeText, Integer, DateTime, \
                             Boolean, Float
from sqlalchemy.orm import scoped_session, sessionmaker, relation, backref, \
                           synonym

from tg import config


DBSession = scoped_session(sessionmaker(autoflush=True, autocommit=False))

DeclarativeBase = declarative_base()

metadata = DeclarativeBase.metadata

def init_model(engine):
    """Call me before using any of the tables or classes in the model."""
    DBSession.configure(bind=engine)

# This is the association table for the many-to-many relationship between
# groups and permissions.
group_permission_table = Table('tg_group_permission', metadata,
    Column('group_id', Integer, ForeignKey('tg_group.group_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    Column('permission_id', Integer, ForeignKey('tg_permission.permission_id',
        onupdate="CASCADE", ondelete="CASCADE"))
)

# This is the association table for the many-to-many relationship between
# groups and members - this is, the memberships.
user_group_table = Table('tg_user_group', metadata,
    Column('user_id', Integer, ForeignKey('tg_user.user_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    Column('group_id', Integer, ForeignKey('tg_group.group_id',
        onupdate="CASCADE", ondelete="CASCADE"))
)

# auth model

class Group(DeclarativeBase):
    """An ultra-simple group definition.
    """
    __tablename__ = 'tg_group'

    group_id = Column(Integer, autoincrement=True, primary_key=True)

    group_name = Column(Unicode(16), unique=True)

    users = relation('User', secondary=user_group_table, backref='groups')

    def __init__(self, group_name=None, display_name=u''):
        if group_name is not None:
            self.group_name = group_name
        self.display_name = display_name


    def __repr__(self):
        return '<Group: name=%s>' % self.group_name


class User(DeclarativeBase):
    """Reasonably basic User definition. Probably would want additional
    attributes.
    """
    __tablename__ = 'tg_user'

    user_id = Column(Integer, autoincrement=True, primary_key=True)

    user_name = Column(Unicode(16), unique=True)

    _password = Column('password', Unicode(40))

    def __repr__(self):
        return '<User: user id="%s", user name="%s">' % (
                self.user_id, self.user_name)

    @property
    def permissions(self):
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms


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

    password = synonym('password', descriptor=property(_get_password,
                                                       _set_password))

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


class Permission(DeclarativeBase):
    """A relationship that determines what each Group can do
    """
    __tablename__ = 'tg_permission'

    permission_id = Column(Integer, autoincrement=True, primary_key=True)

    permission_name = Column(Unicode(16), unique=True)

    groups = relation(Group, secondary=group_permission_table,
                      backref='permissions')
