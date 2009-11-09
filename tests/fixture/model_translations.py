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
Mock SQLAlchemy-powered model definition, with custom attributes which need to
be "translated".

"""

from hashlib import sha1

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import Unicode, Integer
from sqlalchemy.orm import scoped_session, sessionmaker, relation, synonym


DBSession = scoped_session(sessionmaker(autoflush=True, autocommit=False))

DeclarativeBase = declarative_base()

metadata = DeclarativeBase.metadata

def init_model(engine):
    """Call me before using any of the tables or classes in the model."""
    DBSession.configure(bind=engine)

# This is the association table for the many-to-many relationship between
# groups and permissions.
group_permission_table = Table('team_rights', metadata,
    Column('team_id', Integer, ForeignKey('team.team_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    Column('right_id', Integer, ForeignKey('right.right_id',
        onupdate="CASCADE", ondelete="CASCADE"))
)

# This is the association table for the many-to-many relationship between
# groups and members - this is, the memberships.
user_group_table = Table('member_team', metadata,
    Column('member_id', Integer, ForeignKey('member.member_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    Column('team_id', Integer, ForeignKey('team.team_id',
        onupdate="CASCADE", ondelete="CASCADE"))
)

# auth model

class Team(DeclarativeBase):
    
    __tablename__ = "team"

    team_id = Column(Integer, autoincrement=True, primary_key=True)

    team_name = Column(Unicode(16), unique=True)

    members = relation('Member', secondary=user_group_table, backref='teams')


class Member(DeclarativeBase):
    """Reasonably basic User definition. Probably would want additional
    attributes.
    """
    
    __tablename__ = "member"

    member_id = Column(Integer, autoincrement=True, primary_key=True)

    member_name = Column(Unicode(16), unique=True)

    _password = Column('password', Unicode(40))

    def _set_password(self, password):
        """encrypts password on the fly."""
        self._password = self.__encrypt_password(password)

    def _get_password(self):
        """returns password"""
        return self._password

    password = synonym('password', descriptor=property(_get_password,
                                                       _set_password))

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


class Right(DeclarativeBase):
    """A relationship that determines what each Group can do
    """
    
    __tablename__ = "right"

    right_id = Column(Integer, autoincrement=True, primary_key=True)

    right_name = Column(Unicode(16), unique=True)

    teams = relation(Team, secondary=group_permission_table,
                      backref='rights')
