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


""" Not implemented yet (Nakala API)
class Select2ImagesWidget(SelectField):
    def __init__(self, label=None, validators=None, **kwargs):
        response = requests.get('https://apitest.nakala.fr/collections/10.34847%2Fnkl.f48a8c4a/datas',
                                headers={"X-API-KEY": ""})
        choices = [Markup(f"{file['name']} | {file['sha1']}") for data in response.json()['data'] for file in data['files']]
        coerce = str
        kwargs['widget'] = Select2Widget()
        kwargs['render_kw'] = {'onchange': 'fetchCorrectUrlStringFromKbSelect(this)'}
        super(Select2ImagesWidget, self).__init__(label, validators, coerce, choices, **kwargs)
"""