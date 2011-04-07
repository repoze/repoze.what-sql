***************************************
:mod:`repoze.what.plugins.sql` releases
***************************************

This document describes the releases of :mod:`repoze.what.plugins.sql`.


Unreleased
==========

Made compatible with SQLAlchemy 0.7b2, by replacing import from
:mod:`sqlalchemy.exceptions` with :mod:`sqlalchemy.exc`.


Version 1.0 Final (2010-03-11)
==============================

Removed the test suite and the documentation from the final distribution.


Version 1.0rc1 (2009-01-30)
===========================

* Moved :mod:`repoze.what.plugins.quickstart` into an independent project.


Version 1.0b1 (2009-01-27)
==========================

* Synchronized to :mod:`repoze.what` v1.0.1 and its ``credentials`` dict.
* Loaded the user object into the ``identity`` thanks to
  :class:`repoze.who.plugins.sa.SQLAlchemyUserMDPlugin`.
* Many minor fixes.


Version 1.0a5 (2009-01-08)
==========================

* I replaced ``/logout_handler`` with ``/logout`` by mistake while making that
  setting customizable in the previous release, which broke some applications.
  That's now fixed (``/logout_handler`` is back).


Version 1.0a4 (2009-01-02)
==========================

* Added the ability to customize the login/logout related URLs through
  :func:`repoze.what.plugins.quickstart.setup_sql_auth`
  (`TurboGears Ticket #2114 <http://trac.turbogears.org/ticket/2114>`_).


Version 1.0a3 (2008-12-19)
==========================

* Moved the :class:`repoze.what.plugins.quickstart.SQLAuthenticatorPlugin`
  authenticator into a new, :mod:`repoze.what`-independent project:
  :mod:`repoze.who.plugins.sa`.
* :class:`repoze.what.plugins.sql.adapters.SqlGroupsAdapter` ignored
  translations while retrieving the groups to which the authenticated user
  belongs (`TurboGears Ticket #2094 <http://trac.turbogears.org/ticket/2094>`_).
* The documentation for this plugin has been updated and is now hosted at
  http://code.gustavonarea.net/repoze.what.plugins.sql/


Version 1.0a2 (2008-12-04)
==========================

* Fixed the broken test suite for Elixir, thanks to Helio Pereira.
* Updated :func:`repoze.what.plugins.quickstart.setup_sql_auth` according
  to the backwards incompatible change on
  :func:`repoze.what.middleware.setup_auth` introduced in
  :mod:`repoze.what`-1.0b2.
* Now it's possible to customize the authentication/identification cookie
  through :func:`repoze.what.plugins.quickstart.setup_sql_auth`.
* Tons of minor bug fixes.
