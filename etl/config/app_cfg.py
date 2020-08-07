# -*- coding: utf-8 -*-
"""
Global configuration file for TG2-specific settings in etl.

This file complements development/deployment.ini.

"""
from tg.configuration import AppConfig, milestones
import etl
from etl import model, lib

import tg

base_config = AppConfig()
base_config.renderers = []

# True to prevent dispatcher from striping extensions
# For example /socket.io would be served by "socket_io"
# method instead of "socket".
base_config.disable_request_extensions = False

# Set None to disable escaping punctuation characters to "_"
# when dispatching methods.
# Set to a function to provide custom escaping.
base_config.dispatch_path_translator = True

base_config.prefer_toscawidgets2 = True

base_config.package = etl

# Enable json in expose
base_config.renderers.append('json')
# Enable genshi in expose to have a lingua franca
# for extensions and pluggable apps.
# You can remove this if you don't plan to use it.
base_config.renderers.append('kajiki')
base_config.renderers.append('genshi')

# Set the default renderer
base_config.default_renderer = 'kajiki'
# Configure the base SQLALchemy Setup
base_config.use_sqlalchemy = True
base_config.model = etl.model
base_config.DBSession = etl.model.DBSession
# Configure the authentication backend
base_config.auth_backend = 'sqlalchemy'
# YOU MUST CHANGE THIS VALUE IN PRODUCTION TO SECURE YOUR APP
base_config.sa_auth.cookie_secret = "ced31a37-1d1c-4fe1-8de9-6c231bafc11a"
# what is the class you want to use to search for users in the database
base_config.sa_auth.user_class = model.User

from tg.configuration.auth import TGAuthMetadata


# This tells to TurboGears how to retrieve the data for your user
class ApplicationAuthMetadata(TGAuthMetadata):
    def __init__(self, sa_auth):
        self.sa_auth = sa_auth

    def authenticate(self, environ, identity):
        login = identity['login']
        user = self.sa_auth.dbsession.query(self.sa_auth.user_class).filter_by(
            user_name=login
        ).first()

        if not user:  # pragma: no cover
            login = None
        elif not user.validate_password(identity['password']):
            login = None

        if login is None:
            try:
                from urllib.parse import parse_qs, urlencode
            except ImportError:  # pragma: no cover
                from urlparse import parse_qs
                from urllib import urlencode
            from tg.exceptions import HTTPFound

            params = parse_qs(environ['QUERY_STRING'])
            params.pop('password', None)  # Remove password in case it was there
            if user is None:  # pragma: no cover
                params['failure'] = 'user-not-found'
            else:
                params['login'] = identity['login']
                params['failure'] = 'invalid-password'

            # When authentication fails send user to login page.
            environ['repoze.who.application'] = HTTPFound(
                location='?'.join(('/login', urlencode(params, True)))
            )

        return login

    def get_user(self, identity, userid):
        return self.sa_auth.dbsession.query(self.sa_auth.user_class).filter_by(
            user_name=userid
        ).first()

    def get_groups(self, identity, userid):
        return [g.group_name for g in identity['user'].groups]

    def get_permissions(self, identity, userid):
        return [p.permission_name for p in identity['user'].permissions]

base_config.sa_auth.dbsession = model.DBSession

base_config.sa_auth.authmetadata = ApplicationAuthMetadata(base_config.sa_auth)

# In case ApplicationAuthMetadata didn't find the user discard the whole identity.
# This might happen if logged-in users are deleted.
base_config['identity.allow_missing_user'] = False

# You can use a different repoze.who Authenticator if you want to
# change the way users can login
# base_config.sa_auth.authenticators = [('myauth', SomeAuthenticator()]

# You can add more repoze.who metadata providers to fetch
# user metadata.
# Remember to set base_config.sa_auth.authmetadata to None
# to disable authmetadata and use only your own metadata providers
# base_config.sa_auth.mdproviders = [('myprovider', SomeMDProvider()]

# override this if you would like to provide a different who plugin for
# managing login and logout of your application
base_config.sa_auth.form_plugin = None

# You may optionally define a page where you want users to be redirected to
# on login:
base_config.sa_auth.post_login_url = '/post_login'

# You may optionally define a page where you want users to be redirected to
# on logout:
base_config.sa_auth.post_logout_url = '/post_logout'

def enable_debugbar():
    try:
        # Enable DebugBar if available, install tgext.debugbar to turn it on
        if not tg.config.get("disabled_debugbar", False):
            from tgext.debugbar import enable_debugbar
            enable_debugbar(base_config)
    except ImportError:  # pragma: no cover
        pass

milestones.config_ready.register(enable_debugbar)


import tgext.evolve
from etl.config.evolutions.e01_options_dict import EvolveOptionsDict
from etl.config.evolutions.tgappcategories import CategoriesPermissions
from etl.config.evolutions.dashboard_creation import DashboardCreationEvolution
tgext.evolve.plugme(base_config, options={
    'evolutions': [
        EvolveOptionsDict,
        CategoriesPermissions,
        DashboardCreationEvolution,
    ],
})


from tgext.pluggable import plug
plug(base_config, 'tgappcategories', 'categories', global_models=True, plug_bootstrap=True)

from tgext.webassets import Bundle
plug(
    base_config,
    'tgext.webassets',
    # debug=True,
    bundles={
        'js_all': Bundle(
            'javascript/jquery.1.11.1.min.js',
            'javascript/jquery.tablesorter.min.js',
            'javascript/bootstrap.min.js',
            'javascript/toastr.min.js',
            'javascript/bokeh-2.1.1.js',
            'javascript/jets.min.js',
            # with ractive we're stuck because since 0.10.0 there is a TypeError: _0 is not a function
            'javascript/ractive.min.js',
            'javascript/ractive-transitions-slide.min.js',
            'javascript/codemirror/codemirror.min.js',
            'javascript/codemirror/sql.min.js',
            'javascript/codemirror/sql-hint.min.js',
            'javascript/codemirror/javascript.min.js',
            'javascript/codemirror/javascript-hint.min.js',
            'javascript/axw-req.js',
            filters='rjsmin',
            output='assets/js_all.js'
        ),
        'css_all': Bundle(
            'css/bootstrap.min.css',
            'css/fontawesome.all.min.css',
            'css/toastr.min.css',
            'css/codemirror.min.css',
            'css/style.css',
            'css/editor.css',
            filters='rcssmin',
            output='assets/css_all.css',
        ),
    },
)

def enable_depot():
    import logging
    log = logging.getLogger('molepaw.depot')

    # DEPOT setup
    from depot.manager import DepotManager

    storages = {
        'category_images': 'category_image',
    }

    for storage in storages:
        prefix = 'depot.%s.' % storage
        log.info('Configuring Storage %s*', prefix)
        DepotManager.configure(storage, tg.config, prefix)
        DepotManager.alias(storages[storage], storage)


milestones.config_ready.register(enable_depot)
