***************************************
:mod:`repoze.what.plugins.sql` releases
***************************************

This document describes the releases of :mod:`repoze.what.plugins.sql`.


.. _repoze.what-sql-1.0a3:

:mod:`repoze.what.plugins.sql` 1.0a3 (*unreleased*)
===================================================
* Moved the :class:`repoze.what.plugins.quickstart.SQLAuthenticatorPlugin`
  authenticator into a new, :mod:`repoze.what`-independent project:
  :mod:`repoze.who.plugins.sa`.


.. _repoze.what-sql-1.0a2:

:mod:`repoze.what.plugins.sql` 1.0a2 (2008-12-04)
=================================================

* Fixed the broken test suite for Elixir, thanks to Helio Pereira.
* Updated :func:`repoze.what.plugins.quickstart.setup_sql_auth` according
  to the backwards incompatible change on
  :func:`repoze.what.middleware.setup_auth` introduced in
  :mod:`repoze.what`-1.0b2.
* Now it's possible to customize the authentication/identification cookie
  through :func:`repoze.what.plugins.quickstart.setup_sql_auth`.
* Tons of minor bug fixes.
