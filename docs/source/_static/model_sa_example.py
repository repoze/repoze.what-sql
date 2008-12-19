"""
Sample SQLAlchemy-powered model definition for the repoze.what SQL plugin.

This model definition has been taken from a quickstarted TurboGears 2 project,
but it's absolutely independent of TurboGears.

"""

import md5
import sha
from datetime import datetime

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import String, Unicode, UnicodeText, Integer, DateTime, \
                             Boolean, Float
from sqlalchemy.orm import relation, backref, synonym

from yourproject.model import DeclarativeBase, metadata, DBSession


# This is the association table for the many-to-many relationship between
# groups and permissions.
group_permission_table = Table('group_permission', metadata,
    Column('group_id', Integer, ForeignKey('group.group_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    Column('permission_id', Integer, ForeignKey('permission.permission_id',
        onupdate="CASCADE", ondelete="CASCADE"))
)

# This is the association table for the many-to-many relationship between
# groups and members - this is, the memberships.
user_group_table = Table('user_group', metadata,
    Column('user_id', Integer, ForeignKey('user.user_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    Column('group_id', Integer, ForeignKey('group.group_id',
        onupdate="CASCADE", ondelete="CASCADE"))
)

# auth model

class Group(DeclarativeBase):
    """An ultra-simple group definition.
    """
    __tablename__ = 'group'

    group_id = Column(Integer, autoincrement=True, primary_key=True)

    group_name = Column(Unicode(16), unique=True)

    users = relation('User', secondary=user_group_table, backref='groups')


class User(DeclarativeBase):
    """Reasonably basic User definition. Probably would want additional
    attributes.
    """
    __tablename__ = 'user'

    user_id = Column(Integer, autoincrement=True, primary_key=True)
    
    user_name = Column(Unicode(16), unique=True)

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
        """Hash the given password with SHA1.
        
        Edit this method to implement your own algorithm.
        
        """
        hashed_password = password

        if isinstance(password, unicode):
            password_8bit = password.encode('UTF-8')

        else:
            password_8bit = password

        hashed_password = sha.new(password_8bit).hexdigest()

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


class Permission(DeclarativeBase):
    """A relationship that determines what each Group can do"""
    __tablename__ = 'permission'

    permission_id = Column(Integer, autoincrement=True, primary_key=True)

    permission_name = Column(Unicode(16), unique=True)

    groups = relation(Group, secondary=group_permission_table,
                      backref='permissions')
