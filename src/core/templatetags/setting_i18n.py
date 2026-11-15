"""
BTE: runtime translation of Setting pretty names / descriptions.

Setting.pretty_name and Setting.description are stored in the database and are
not registered with modeltranslation. Their English texts are listed in
core/setting_strings.py (gettext_noop) so makemessages keeps them in the .po
files; this filter looks them up in the active language.

    {% load setting_i18n %}
    {{ setting.pretty_name|setting_trans }}
"""

from django import template
from django.utils.safestring import SafeData, mark_safe
from django.utils.translation import gettext

register = template.Library()


def translate_setting_text(value):
    """gettext() for DB setting texts. Empty values are returned unchanged,
    because gettext("") would return the .po header."""
    if not value or not isinstance(value, str):
        return value
    translated = gettext(value)
    return mark_safe(translated) if isinstance(value, SafeData) else translated


@register.filter
def setting_trans(value):
    return translate_setting_text(value)
