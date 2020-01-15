# -*- coding: utf-8 -*-
import json

from tgext.evolve import Evolution
from sqlalchemy import create_engine
from etl.model import DBSession, Dashboard, DeclarativeBase
import transaction
import logging
from tg import config

log = logging.getLogger('molepaw')


class DashboardCreationEvolution(Evolution):
    evolution_id = 'DashboardCreationEvolution'

    def evolve(self):
        log.info('DashboardCreationEvolution migration running')

        engine = create_engine(config.get('sqlalchemy.url'), echo=True)
        DeclarativeBase.metadata.create_all(engine)
        
        main = Dashboard()
        main.name = 'main dashboard'
        DBSession.add(main)
        
        DBSession.flush()
        transaction.commit()

