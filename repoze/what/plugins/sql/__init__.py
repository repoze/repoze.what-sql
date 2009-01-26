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

"""SQL plugin for repoze.what based on SQLAlchemy."""

from repoze.what.plugins.sql.adapters import SqlGroupsAdapter, \
                                             SqlPermissionsAdapter, \
                                             configure_sql_adapters

__all__ = ['SqlGroupsAdapter', 'SqlPermissionsAdapter',
           'configure_sql_adapters']
