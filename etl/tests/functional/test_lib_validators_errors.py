import transaction
from etl.tests.functional.controllers import BaseTestController
from etl.lib import validators
from nose.tools import assert_raises
from mock import patch, PropertyMock
from etl import model
from formencode.api import Invalid
from tw2.core import ValidationError
from tg.wsgiapp import TemplateContext
from tg.exceptions import HTTPPreconditionFailed
import json
from etl.lib.utils import is_api_authenticated
from tg.configuration.tgconfig import _DispatchingConfigWrapper
from tg.predicates import NotAuthorizedError


class TestValidatorsErrors(BaseTestController):

    @patch('etl.lib.validators.tmpl_context', spec=TemplateContext)
    def test_merge_validator_errors_and_corners(self, tmpl_mock):

        validator = validators.MergeValidator(
            'datasetid', 'join_type', 'join_self_col', 'join_other_col'
        )

        assert validator._validate_python(
            {'datasetid': self.dataset}
        ) is None

        type(tmpl_mock).extraction = PropertyMock(
            return_value=model.DBSession.query(model.Extraction).get(self.extraction)
        )

        assert_raises(
            Invalid,
            validator._validate_python,
            {
                'datasetid': self.dataset,
                'join_type': 'left',
                'join_other_col': 'user_id',
                'join_self_col': 'display_name'
            }
        )

    def test_json_validator(self):
        validator = validators.JSONValidator()

        assert validator._validate_python(
            json.dumps({"key": "value"})
        ) is None

        assert_raises(
            ValidationError,
            validator._validate_python,
            'pippo, {"pluto}'
        )

    def test_comma_separated_list_validator(self):
        validator = validators.CommaSeparatedListValidator()

        assert validator._convert_to_python(
            'uno,due,tre'
        ) == ['uno', 'due', 'tre']

        assert validator._convert_from_python(
            ['uno', 'due', 'tre']
        ) == 'uno,due,tre'

    def test_visualization_type_validator_error(self):
        validator = validators.VisualizationTypeValidator()

        assert_raises(
            ValidationError,
            validator._validate_python,
            {'type': 'wrong_type'}
        )

    def get_extraction(self):
        return model.DBSession.query(
            model.Extraction
        ).get(self.extraction)

    def tests_validate_axis_against_extraction_visualization_errors(self):
        from etl.model.dataset import DST_CACHE
        extraction = self.get_extraction()

        # wrong axis
        assert_raises(
            HTTPPreconditionFailed,
            validators.validate_axis_against_extraction_visualization,
            'histogram',
            'wrong_one,user_id',
            extraction
        )

        # x axes not a string
        assert_raises(
            HTTPPreconditionFailed,
            validators.validate_axis_against_extraction_visualization,
            'histogram',
            'user_id,display_name',
            extraction
        )

        # x axes duplicated
        extraction.sample['display_name'][1] = 'Example Admin'
        assert_raises(
            HTTPPreconditionFailed,
            validators.validate_axis_against_extraction_visualization,
            'histogram',
            'display_name,display_name',
            extraction
        )
        DST_CACHE.clear()

        # x wrong type
        assert_raises(
            HTTPPreconditionFailed,
            validators.validate_axis_against_extraction_visualization,
            'linechart',
            'display_name,display_name',
            extraction
        )

        # x duplicated
        extraction.sample['created'][1] = extraction.sample['created'][0]
        assert_raises(
            HTTPPreconditionFailed,
            validators.validate_axis_against_extraction_visualization,
            'linechart',
            'created,display_name',
            extraction
        )
        DST_CACHE.clear()

        assert_raises(
            HTTPPreconditionFailed,
            validators.validate_axis_against_extraction_visualization,
            'pie',
            'user_id,display_name',
            extraction
        )


class TestUtilRemaingLines(BaseTestController):

    @patch('etl.lib.utils.config')
    def tests_is_api_authentication(self, mockconfig):
        environ = {
            'QUERY_STRING': 'not met'
        }
        predicate = is_api_authenticated()
        assert_raises(
            NotAuthorizedError,
            predicate.evaluate,
            environ,
            'credentials'
        )
