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

"""Stuff required to setup the test database."""

import os
import sha

from sqlalchemy import *
from sqlalchemy.orm import *
from cStringIO import StringIO
from cgi import FieldStorage
import elixir

from fixture.model_elixir import init_model, DBSession, metadata, Permission, \
                                 Group, User

engine = create_engine(os.environ.get('DBURL', 'sqlite://'))

def setup_database():
    init_model(engine)
    teardownDatabase()
    elixir.setup_all(True)

    # Creating permissions

    see_site = Permission()
    see_site.permission_name = u'see-site'
    see_site.description = u'see-site permission description'
    DBSession.save(see_site)

    edit_site = Permission()
    edit_site.permission_name = u'edit-site'
    edit_site.description = u'edit-site permission description'
    DBSession.save(edit_site)

    commit = Permission()
    commit.permission_name = u'commit'
    commit.description = u'commit permission description'
    DBSession.save(commit)

    # Creating groups

    admins = Group()
    admins.group_name = u'admins'
    admins.display_name = u'Admins Group'
    admins.permissions.append(edit_site)
    DBSession.save(admins)

    developers = Group(group_name=u'developers',
                       display_name=u'Developers Group')
    developers.permissions = [commit, edit_site]
    DBSession.save(developers)

    trolls = Group(group_name=u'trolls', display_name=u'Trolls Group')
    trolls.permissions.append(see_site)
    DBSession.save(trolls)

    # Plus a couple of groups with no permissions
    php = Group(group_name=u'php', display_name=u'PHP Group')
    DBSession.save(php)

    python = Group(group_name=u'python', display_name=u'Python Group')
    DBSession.save(python)

    # Creating users

    user = User()
    user.user_name = u'rms'
    user.password = u'freedom'
    user.email_address = u'someone@fsf.ext'
    user.groups.append(admins)
    user.groups.append(developers)
    DBSession.save(user)

    user = User()
    user.user_name = u'linus'
    user.password = u'linux'
    user.email_address = u'someone@linux.ext'
    user.groups.append(developers)
    DBSession.save(user)

    user = User()
    user.user_name = u'sballmer'
    user.password = u'developers'
    user.email_address = u'developer@developers.dev'
    user.groups.append(trolls)
    DBSession.save(user)

    # Plus a couple of users without groups
    user = User()
    user.user_name = u'guido'
    user.password = u'phytonic'
    user.email_address = u'someone@python.ext'
    DBSession.save(user)

    user = User()
    user.user_name = u'rasmus'
    user.password = u'php'
    user.email_address = u'someone@php.ext'
    DBSession.save(user)

    DBSession.commit()


def teardownDatabase():
    DBSession.rollback()
    metadata.drop_all(engine)
