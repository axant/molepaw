from etl.tests import TestController
from etl.model import DBSession
from etl import model
import json
import transaction
from tgext.pluggable import app_model
from etl.model.datasource import reset_cache
from random import randint


class BaseTestController(TestController):
    datasource = None
    dataset = None
    extraction = None
    filter = None
    step = None
    category = None
    extractiondataset = None
    filter_data = dict(
        name='custom_flt',
        default=True,
        query="user_name != 'viewer'"
    )

    def setUp(self):
        reset_cache()
        super(BaseTestController, self).setUp()
        cat = app_model.Category(
            name='Default category 1'
        )
        DBSession.add(cat)
        DBSession.flush()
        ds = self.create_datasource(
            name='default_ds'
        )
        DBSession.flush()
        dt = self.create_dataset(
            ds, name='default_dts'
        )
        DBSession.flush()
        ext = self.create_extraction(
            name='default_ext',
            category=cat
        )
        DBSession.flush()
        extdt = model.ExtractionDataSet(
            dataset_id=dt.uid,
            extraction_id=ext.uid
        )
        DBSession.add(extdt)
        flt = model.ExtractionFilter(
            extraction_id=ext.uid,
            name='default_flt',
            default=True
        )
        DBSession.add(flt)
        DBSession.flush()
        step = model.ExtractionStep(
            priority=0,
            function='query',
            options=json.dumps({
                'expression': self.filter_data['query']
            }),
            extraction_filter_id=flt.uid,
            extraction_id=ext.uid
        )
        DBSession.add(step)
        DBSession.flush()
        self.datasource = ds.uid
        self.dataset = dt.uid
        self.extraction = ext.uid
        self.filter = flt.uid
        self.step = step.uid
        self.category = cat._id
        self.extractiondataset = extdt.uid
        transaction.commit()
