from tw2.core import Widget
from tw2.forms import TextArea


class SmartWidgetTypes(dict):
    """
    Hack to make so that widgets appear only in Sprox FORMs
    and never inside Tables.
    """
    def get(self, k, d=None):
        if d is Widget:
            return d
        return super(SmartWidgetTypes, self).get(k, d)


class CodeTextArea(TextArea):
    type = 'sql'

    def prepare(self):
        super(CodeTextArea, self).prepare()
        if not self.attrs.get('class'):
            self.attrs['class'] = ''
        self.attrs['class'] += ' codetextarea-'+self.type
