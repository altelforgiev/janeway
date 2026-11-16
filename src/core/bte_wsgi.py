"""
WSGI entry point for gunicorn on btejournal.kz.

core.custom_settings starts with `from core.janeway_global_settings import *`, so
Janeway's settings loader (utils.load_janeway_settings) merges INSTALLED_APPS twice
and Django refuses to start ("Application labels aren't unique: modeltranslation").
src/manage.py works around this with a hook around django.setup(); runserver goes
through manage.py, gunicorn does not. This module applies the same hook (logic kept
identical to src/manage.py) and then loads Janeway's standard core.wsgi.
"""
import os

import django

os.environ.setdefault("JANEWAY_SETTINGS_MODULE", "core.custom_settings")

_original_setup = django.setup


def _safe_setup(*args, **kwargs):
    from django.conf import settings

    cleaned = []
    seen = set()
    has_custom_admin = any("AdminConfig" in a for a in settings.INSTALLED_APPS)
    for app in settings.INSTALLED_APPS:
        if "modeltranslation" in app:
            label = "modeltranslation"
        elif "admin" in app:
            label = "admin"
        else:
            label = app
        if app == "django.contrib.admin" and has_custom_admin:
            continue
        if label not in seen:
            cleaned.append(app)
            seen.add(label)
    settings.INSTALLED_APPS = cleaned
    _original_setup(*args, **kwargs)


django.setup = _safe_setup

from core.wsgi import application  # noqa: E402,F401