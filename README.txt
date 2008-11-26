*********************************
The :mod:`repoze.what` SQL plugin
*********************************

This is an adapters and extras plugin for repoze.what.

The SQL plugin makes repoze.what support sources defined in SQLAlchemy-managed 
databases by providing one group adapter, one permission adapter and one 
utility to configure both in one go (optionally, when the group source and the 
permission source have a relationship).
    
This plugin also defines repoze.what.plugins.quickstart.
