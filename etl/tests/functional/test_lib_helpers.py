from etl.tests import TestController
from etl.lib import helpers as h
from etl.lib.widgets import SmartWidgetTypes, CodeTextArea
from tw2.forms import TextArea
from tw2.core import Widget


class TestLibHelpersAndWidgets(TestController):

    def test_icon(self):
        assert h.icon('icon') == '<i class="glyphicon glyphicon-icon"></i>'

    def test_dashboard(self):
        assert h.dashboards() == []

    def test_smart_widget(self):
        s = SmartWidgetTypes()
        s['sample'] = 'something'
        assert s.get('sample') == 'something'
        assert s.get('sample', d=Widget) is Widget

    def test_text_area(self):
        t1 = super(Widget, CodeTextArea).__new__(CodeTextArea(template='none'))
        t1.prepare()
        assert t1.attrs['class'] == ' codetextarea-sql'
