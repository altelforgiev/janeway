#!/usr/bin/env python

import os
import sys

from django.conf import settings

from utils import load_janeway_settings

os.environ.setdefault("JANEWAY_SETTINGS_MODULE", "core.custom_settings")

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    import django

    # --- СТАРТ ПЕРЕХВАТЧИКА JANEWAY ---
    original_setup = django.setup

    def safe_setup(*args, **kwargs):
        from django.conf import settings
        cleaned = []
        seen = set()

        # Проверяем наличие кастомной админки Janeway
        has_custom_admin = any("AdminConfig" in a for a in settings.INSTALLED_APPS)

        for app in settings.INSTALLED_APPS:
            # Считываем метки проблемных приложений
            if "modeltranslation" in app:
                label = "modeltranslation"
            elif "admin" in app:
                label = "admin"
            else:
                label = app

            # Убиваем конфликт админок
            if app == "django.contrib.admin" and has_custom_admin:
                continue

            # Пропускаем любые дубликаты, которые склеил загрузчик Janeway
            if label not in seen:
                cleaned.append(app)
                seen.add(label)

        # Перезаписываем финальный список и даем Django зеленый свет
        settings.INSTALLED_APPS = cleaned
        original_setup(*args, **kwargs)


    # Подменяем стандартный запуск нашим безопасным
    django.setup = safe_setup
    # --- КОНЕЦ ПЕРЕХВАТЧИКА ---

    load_janeway_settings()
    execute_from_command_line(sys.argv)
