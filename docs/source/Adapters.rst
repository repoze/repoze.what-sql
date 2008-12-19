**************************************
:mod:`repoze.what` SQL source adapters
**************************************

.. module:: repoze.what.plugins.sql.adapters
    :synopsis: SQL adapters for repoze.what
.. moduleauthor:: Gustavo Narea <me@gustavonarea.net>

.. topic:: Overview

    This document explains the SQL source adapters provided by the plugin.

The classes and functions mentioned below are imported into the 
:mod:`repoze.what.plugins.sql` namespace, so you can also import them from
there.


SQL adapters
============

.. autoclass:: SqlGroupsAdapter
    :members: __init__

.. autoclass:: SqlPermissionsAdapter
    :members: __init__


Utilities
=========

.. autofunction:: configure_sql_adapters
    