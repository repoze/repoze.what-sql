*********************************
The :mod:`repoze.what` SQL plugin
*********************************

:Author: Gustavo Narea.
:Status: Official
:Latest release: |release|

.. module:: repoze.what.plugins.sql
    :synopsis: SQL support for repoze.what
.. moduleauthor:: Gustavo Narea <me@gustavonarea.net>
.. moduleauthor:: Florent Aide <florent.aide@gmail.com>
.. moduleauthor:: Agendaless Consulting and Contributors

.. topic:: Overview

    The SQL plugin makes :mod:`repoze.what` support sources 
    defined in `SQLAlchemy <http://www.sqlalchemy.org/>`_ or `Elixir 
    <http://elixir.ematia.de/>`_-managed databases by 
    providing one *group adapter*, one *permission adapter* and 
    one utility to configure both in one go (optionally, when the 
    *group source* and the *permission source* have a 
    relationship). They are all defined in the :mod:`repoze.what.plugins.sql` 
    module.
    
    This plugin also defines :mod:`repoze.what.plugins.quickstart`.
    
    .. warning::
    
        Only SQLAlchemy is intended to be supported. Elixir
        is known to work but it's not officially supported, so Elixir support
        *might* be broken in future releases.


How to install
==============

The minimum requirements are SQLAlchemy, :mod:`repoze.who.plugins.sa`
and :mod:`repoze.what`, and you can install it all with ``easy_install``::
    
        easy_install repoze.what.plugins.sql


How to get help?
================

The prefered place to ask questions is the `Repoze mailing list 
<http://lists.repoze.org/listinfo/repoze-dev>`_ or the `#repoze 
<irc://irc.freenode.net/#repoze>`_ IRC channel. Bugs reports and feature 
requests should be sent to `the issue tracker of the Repoze project 
<http://bugs.repoze.org/>`_.

Contents
========

.. toctree::
    :maxdepth: 2

    Adapters
    Quickstart
    News


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
