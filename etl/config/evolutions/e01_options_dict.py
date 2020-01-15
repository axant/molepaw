# -*- coding: utf-8 -*-
import json

from tgext.evolve import Evolution
from etl.model import ExtractionStep, DBSession
import transaction


class EvolveOptionsDict(Evolution):
    evolution_id = '01_EvolveOptionsDict'

    def evolve(self):
        for step in DBSession.query(ExtractionStep).filter_by(function='slice').all():
            options = json.loads(step.options)
            if isinstance(options, list):
                step.options = json.dumps({'fields': options})

        for step in DBSession.query(ExtractionStep).filter_by(function='concatcols').all():
            options = json.loads(step.options)
            if isinstance(options, list):
                step.options = json.dumps({'columns': options})

        for step in DBSession.query(ExtractionStep).filter_by(function='setvalue').all():
            options = json.loads(step.options)
            if isinstance(options, list):
                step.options = json.dumps({'field': options[0],
                                           'value': options[1]})

        for step in DBSession.query(ExtractionStep).filter_by(function='striptime').all():
            options = json.loads(step.options)
            if isinstance(options, list):
                step.options = json.dumps({'field': options[0]})

        for step in DBSession.query(ExtractionStep).filter_by(function='stripday').all():
            options = json.loads(step.options)
            if isinstance(options, list):
                step.options = json.dumps({'field': options[0]})

        for step in DBSession.query(ExtractionStep).filter_by(function='rename').all():
            options = json.loads(step.options)
            if isinstance(options, list):
                step.options = json.dumps({'source': options[0],
                                           'target': options[1]})

        for step in DBSession.query(ExtractionStep).filter_by(function='setindex').all():
            options = json.loads(step.options)
            if isinstance(options, list):
                step.options = json.dumps({'index': options[0]})

        DBSession.flush()
        transaction.commit()
