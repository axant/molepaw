# -*- coding: utf-8 -*-
"""Setup the etl application"""
from __future__ import print_function

from tg import config
import transaction
import logging

logger = logging.getLogger('etl.websetup.schema')


def setup_schema(command, conf, vars):
    """Place any commands to setup etl here"""
    # Load the models

    # <websetup.websetup.schema.before.model.import>
    from etl import model
    # <websetup.websetup.schema.after.model.import>

    # <websetup.websetup.schema.before.metadata.create_all>
    logger.info("Creating tables")
    # import pdb; pdb.set_trace()
    model.metadata.create_all(bind=config['tg.app_globals'].sa_engine)
    # <websetup.websetup.schema.after.metadata.create_all>
    transaction.commit()
    logger.info('Initializing Migrations')
    import alembic.config
    alembic_cfg = alembic.config.Config()
    alembic_cfg.set_main_option("script_location", "migration")
    alembic_cfg.set_main_option("sqlalchemy.url", config['sqlalchemy.url'])
    import alembic.command
    alembic.command.stamp(alembic_cfg, "head")
