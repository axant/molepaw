# -*- coding: utf-8 -*-
"""WSGI middleware initialization for the etl application."""
from depot.manager import DepotManager

from etl.config.app_cfg import base_config
from etl.config.environment import load_environment

__all__ = ['make_app']

# Use base_config to setup the necessary PasteDeploy application factory.
# make_base_app will wrap the TG2 app with all the middleware it needs.
make_base_app = base_config.setup_tg_wsgi_app(load_environment)


def make_app(global_conf, full_stack=True, **app_conf):
    """
    Set etl up with the settings found in the PasteDeploy configuration
    file used.

    :param global_conf: The global settings for etl (those
        defined under the ``[DEFAULT]`` section).
    :type global_conf: dict
    :param full_stack: Should the whole TG2 stack be set up?
    :type full_stack: str or bool
    :return: The etl application with all the relevant middleware
        loaded.

    This is the PasteDeploy factory for the etl application.

    ``app_conf`` contains all the application-specific settings (those defined
    under ``[app:main]``.
    """
    app = make_base_app(global_conf, full_stack=True, **app_conf)

    # Wrap your base TurboGears 2 application with custom middleware here

    # This is needed because during tests we create multiple apps and DEPOT can only have a single middleware.
    DepotManager._middleware = None
    app = DepotManager.make_middleware(app)

    return app
