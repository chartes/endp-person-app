from wtforms import TextAreaField, SelectField
from wtforms.widgets import TextArea
from flask_admin.form.widgets import Select2Widget

class CKTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        if kwargs.get('class'):
            kwargs['class'] += ' ckeditor'
        else:
            kwargs.setdefault('class', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(TextAreaField):
    widget = CKTextAreaWidget()

class QuillTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        if kwargs.get('class'):
            kwargs['class'] += ' quill-editor'
        else:
            kwargs.setdefault('class', 'quill-editor')
        return super(QuillTextAreaWidget, self).__call__(field, **kwargs)

class QuillTextAreaField(TextAreaField):
    widget = QuillTextAreaWidget()


class Select2Dynamic(SelectField):
    widget = Select2Widget()