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

"""Stuff required to setup the test database using translations."""

import os

from sqlalchemy import *
from sqlalchemy.orm import *
from cgi import FieldStorage

from fixture.model_translations import (init_model, DBSession, metadata, Member,
                                        Team, Right)

engine = create_engine(os.environ.get('DBURL', 'sqlite://'))

def setup_database():
    init_model(engine)
    teardownDatabase()
    metadata.create_all(engine)

    # Creating permissions

    see_site = Right()
    see_site.right_name = u'see-site'
    DBSession.add(see_site)

    edit_site = Right()
    edit_site.right_name = u'edit-site'
    DBSession.add(edit_site)

    commit = Right()
    commit.right_name = u'commit'
    DBSession.add(commit)

    # Creating groups

    admins = Team(team_name=u'admins')
    admins.rights.append(edit_site)
    DBSession.add(admins)

    developers = Team(team_name=u'developers')
    developers.rights = [commit, edit_site]
    DBSession.add(developers)

    trolls = Team(team_name=u'trolls')
    trolls.rights.append(see_site)
    DBSession.add(trolls)

    # Plus a couple of groups with no permissions
    php = Team(team_name=u'php')
    DBSession.add(php)

    python = Team(team_name=u'python')
    DBSession.add(python)

    # Creating users

    user = Member()
    user.member_name = u'rms'
    user.password = u'freedom'
    user.teams.append(admins)
    user.teams.append(developers)
    DBSession.add(user)

    user = Member()
    user.member_name = u'linus'
    user.password = u'linux'
    user.teams.append(developers)
    DBSession.add(user)

    user = Member()
    user.member_name = u'sballmer'
    user.password = u'developers'
    user.teams.append(trolls)
    DBSession.add(user)

    # Plus a couple of users without groups
    user = Member()
    user.member_name = u'guido'
    user.password = u'phytonic'
    DBSession.add(user)

    user = Member()
    user.member_name = u'rasmus'
    user.password = u'php'
    DBSession.add(user)

    DBSession.commit()


def teardownDatabase():
    DBSession.rollback()
    metadata.drop_all(engine)

