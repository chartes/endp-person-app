from flask import Markup
from .constants import NAKALA_DATA_IDENTIFIERS


def _markup_interpret(self, context, model, name):
    item = getattr(model, name)
    if item is None:
        item = ""
    return Markup(item)


def _thumbnail_interpret(self, context, model, name):
    item = getattr(model, name)
    if item is None:
        item = ""
    else:
        value = item.split(";")
        img_sha = value[2]
        img_val = value[1]
        register = value[0]
        data_id = NAKALA_DATA_IDENTIFIERS[register]
        item = f"""
        <b>image</b> : {img_val} ({register})  <br>
        <b>id</b> : {data_id} <br>
        <a href="https://nakala.fr/{data_id}#{img_sha}" target="_blank">Visualiser dans Nakala</a>
        """
    return Markup(item)


def _bold_item_list(self, context, model, name):
    item = getattr(model, name)
    return Markup(f"<b>{item}</b>")


def _hyperlink_item_list(self, context, model, name):
    item = getattr(model, name)
    return Markup(f"<a href='{item}' target='_blank'>{item}</a>")


def _color_on_bool(self, context, model, name):
    item = getattr(model, name)
    if item:
        return Markup(f"<span class='glyphicon glyphicon glyphicon-ok' style='color: #2ecc71;'></span>")
    else:
        return Markup(f"<span class='glyphicon glyphicon glyphicon-remove' style='color: #BE0A25;'></span>")


def _dateformat(self, context, model, name):
    item = getattr(model, name)
    return item.strftime("%Y-%m-%d %H:%M:%S")


def _create_tooltip(comment, place):
    return f"""<a data-toggle="tooltip" data-placement="{place}" data-html="true" title="<i>{comment}</i>">
  <i class="fa fa-info-circle"></i>
</a>"""


def _format_label_form_with_tooltip(label, comment, place="bottom"):
    return Markup(f"{label} {_create_tooltip(comment, place)}")
