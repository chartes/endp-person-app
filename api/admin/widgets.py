"""
widgets.py

Widgets or custom fields for views.
"""

from wtforms import SelectField
from flask_admin.form.widgets import Select2Widget

from api.models import (_get_enum_values,
                        KnowledgeBaseLabels)


class Select2DynamicWidget(SelectField):
    def __init__(self, label=None, validators=None, **kwargs):
        choices = [(label, label) for label in _get_enum_values(KnowledgeBaseLabels)]
        coerce = str
        kwargs['widget'] = Select2Widget()
        kwargs['render_kw'] = {'onchange': 'fetchCorrectUrlStringFromKbSelect(this)'}
        super(Select2DynamicWidget, self).__init__(label, validators, coerce, choices, **kwargs)