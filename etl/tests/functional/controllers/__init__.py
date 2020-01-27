from etl.tests import TestController
from etl.model import DBSession
from etl import model
import json
import transaction


class BaseTestController(TestController):
    datasource = None
    dataset = None
    extraction = None
    filter = None
    step = None
    filter_data = dict(
        name='custom_flt',
        default=False,
        query=json.dumps(dict(property={'$ne': None}))
    )

    def setUp(self):
        super(BaseTestController, self).setUp()
        ds = self.create_datasource('default_ds')
        DBSession.add(ds)
        DBSession.flush()
        dt = self.create_dataset(
            ds, 'default_dts'
        )
        DBSession.add(dt)
        DBSession.flush()
        ext = self.create_extraction(name='default_ext')
        DBSession.add(ext)
        DBSession.flush()
        flt = model.ExtractionFilter(extraction_id=ext.uid, name='default_flt')
        DBSession.add(flt)
        DBSession.flush()
        step = model.ExtractionStep(
            priority=0,
            function='query',
            options=json.dumps({
                'expression': self.filter_data['query']
            }),
            extraction_filter_id=flt.uid
        )
        DBSession.add(step)
        DBSession.flush()
        self.datasource = ds.uid
        self.dataset = dt.uid
        self.extraction = ext.uid
        self.filter = flt.uid
        self.step = step.uid
        transaction.commit()
