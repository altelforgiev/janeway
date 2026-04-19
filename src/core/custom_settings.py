# src/core/custom_settings.py
import os
from core.janeway_global_settings import * # Наследуем всё из базового файла
from core import plugin_installed_apps      # Нужно для загрузки локализаций плагинов

# --- Security & Debug ---
SECRET_KEY = os.environ.get("SECRET_KEY", SECRET_KEY)
DEBUG = os.environ.get("DEBUG", "False") == "True"
#ALLOWED_HOSTS = os.environ.get("JANEWAY_ALLOWED_HOSTS", "localhost").split(",")

# --- Security & Debug ---
# Лучше использовать os.environ.get для DEBUG, чтобы на боевом сервере случайно не включить его
DEBUG = os.environ.get("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("JANEWAY_ALLOWED_HOSTS", "localhost").split(",")


# --- Internationalization (Ваши настройки для 3-х языков) ---
LANGUAGE_CODE = "en"

LANGUAGES = (
    ('en', 'English'),
    ('kk', 'Қазақша'),
    ('ru', 'Русский'),
)

MODELTRANSLATION_LANGUAGES = ('en', 'kk', 'ru')
USE_L10N = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, "core", "locales"),
    os.path.join(BASE_DIR, "locale"),
] + plugin_installed_apps.load_plugin_locales(BASE_DIR)


# --- Middleware ---
# Оставляем ваш порядок (LocaleMiddleware поднята выше для правильного перехвата языков)
MIDDLEWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.TimezoneMiddleware",
    "core.middleware.SiteSettingsMiddleware",
    "core.middleware.MaintenanceModeMiddleware",
    "cron.middleware.CronMiddleware",
    "core.middleware.CounterCookieMiddleware",
    "core.middleware.PressMiddleware",
    "core.middleware.GlobalRequestMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "journal.middleware.LanguageMiddleware",
    "hijack.middleware.HijackUserMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
)

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# --- Theme Customization ---
if "BTE" not in CORE_THEMES:
    CORE_THEMES.append("BTE")
INSTALLATION_BASE_THEME = "OLH"


# --- Database ---
if os.environ.get("DB_VENDOR") == "postgres":
    # Используем update(), чтобы безопасно обновить ключи, не затирая другие параметры словаря DATABASES
    DATABASES["default"].update({
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "janeway"),
        "USER": os.environ.get("DB_USER", "janeway_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "janeway-postgres"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    })