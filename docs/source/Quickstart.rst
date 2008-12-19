********************************************************
:mod:`repoze.what.plugins.quickstart` -- Auth quickstart
********************************************************

.. module:: repoze.what.plugins.quickstart
    :synopsis: Ready-to-use authentication and authorization
.. moduleauthor:: Gustavo Narea <me@gustavonarea.net>
.. moduleauthor:: Florent Aide <florent.aide@gmail.com>
.. moduleauthor:: Agendaless Consulting and Contributors


.. topic:: Overview

    Your application may take advantage of a rather simple, and usual, 
    authentication and authorization setup, in which the users' data, the 
    groups and the permissions used in the application are all stored in a 
    SQLAlchemy or Elixir-managed database.


To get started quickly, you may copy the SQLAlchemy-powered model 
defined in `model_sa_example.py 
<http://code.gustavonarea.net/repoze.what.plugins.sql/_static/model_sa_example.py>`_
(or `model_elixir_example.py 
<http://code.gustavonarea.net/repoze.what.plugins.sql/_static/model_elixir_example.py>`_
for Elixir) and then create at least a few rows to try it out::

    u = User()
    u.user_name = u'manager'
    u.password = u'managepass'

    DBSession.save(u)

    g = Group()
    g.group_name = u'managers'

    g.users.append(u)

    DBSession.save(g)

    p = Permission()
    p.permission_name = u'manage'
    p.groups.append(g)

    DBSession.save(p)
    DBSession.flush()

Now that you have some rows in your database, you can set up authentication
and authorization as explained in the next section.

How to set it up
----------------

Although :mod:`repoze.what` is meant to deal with authorization only,
this module configures authentication and identification for you through
:mod:`repoze.who`, so that you can get started quickly (hence the name).

Such a setup is performed by the :func:`setup_sql_auth` function:

.. autofunction:: setup_sql_auth

See "`changing attribute names`_" to learn how to use the ``translations``
argument in :func:`setup_sql_auth`.


Customizing the model definition
--------------------------------

Your auth-related model doesn't `have to` be like the default one, where the
class for your users, groups and permissions are, respectively, ``User``,
``Group`` and ``Permission``, and your users' user name is available in
``User.user_name``. What if you prefer ``Member`` and ``Team`` instead of
``User`` and ``Group``, respectively? Or what if you prefer ``Group.members``
instead of ``Group.users``? Read on!

Changing class names
~~~~~~~~~~~~~~~~~~~~

Changing the name of an auth-related class (``User``, ``Group`` or ``Permission``)
is a rather simple task. Just rename it in your model, and then make sure to
update the parameters you pass to :func:`setup_sql_auth` accordingly.

Changing attribute names
~~~~~~~~~~~~~~~~~~~~~~~~

You can also change the name of the attributes assumed by
:mod:`repoze.what` in your auth-related classes, such as renaming
``User.groups`` to ``User.memberships``.

Changing such values is what :mod:`repoze.what` calls "translating".
You may set the translations for the attributes of the models
:mod:`repoze.what` deals with in a dictionary passed to :func:`setup_sql_auth`
as its ``translations`` parameters. For
example, if you want to replace ``Group.users`` with ``Group.members``, you may
use the following translation dictionary::

    translations['users'] = 'members'

Below are the translations that you would be able to set in the ``translations``
dictionary used above:

    * ``user_name``: The translation for the attribute in ``User.user_name``.
    * ``users``: The translation for the attribute in ``Group.users``.
    * ``group_name``: The translation for the attribute in ``Group.group_name``.
    * ``groups``: The translation for the attribute in ``User.groups`` and
      ``Permission.groups``.
    * ``permission_name``: The translation for the attribute in
      ``Permission.permission_name``.
    * ``permissions``: The translation for the attribute in ``User.permissions``
      and ``Group.permissions``.
    * ``validate_password``: The translation for the method in
      ``User.validate_password``.
