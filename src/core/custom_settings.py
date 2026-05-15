# src/core/custom_settings.py
import os
from core.janeway_global_settings import * # Наследуем всё из базового файла
from core import plugin_installed_apps      # Нужно для загрузки локализаций плагинов

# --- Security & Debug ---
SECRET_KEY = os.environ.get("SECRET_KEY", SECRET_KEY)
# Лучше использовать os.environ.get для DEBUG, чтобы на боевом сервере случайно не включить его
DEBUG = os.environ.get("DEBUG", "False") == "True"
#ALLOWED_HOSTS = os.environ.get("JANEWAY_ALLOWED_HOSTS", "localhost").split(",")

# --- URL Config ---
# Использовать домен для определения журнала (убирает префикс /1/ из URL)
URL_CONFIG = "domain"

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
# --- Настройки SMTP Почты ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Подтягиваем данные из .env
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 25))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

# Преобразуем текстовые "True"/"False" из .env в логические переменные Python
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "False") == "True"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False") == "True"

# От кого будут приходить письма (если не указано явно)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
# Email для ошибок сервера
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# --- Static Files ---
# Добавляем директорию со статикой для темы BTE
STATICFILES_DIRS += (
    os.path.join(BASE_DIR, "themes", "BTE", "static"),
)
