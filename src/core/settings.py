import os
import sys
from pathlib import Path

from celery.schedules import crontab
from dotenv import load_dotenv as loadenv

# ================================================================
# BASE DIRECTORIES
# ================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "apps"))
SITE_ID = 1

# ================================================================
# ENVIRONMENT VARIABLES
# ================================================================
loadenv(dotenv_path=BASE_DIR / ".env")


# ================================================================
# SECURITY
# ================================================================
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
DEBUG = True if os.environ.get("DJANGO_DEBUG", "FALSE") == "TRUE" else False
ALLOWED_HOSTS = [
    host
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host
]
CSRF_TRUSTED_ORIGINS = [
    origin for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if origin
]

SECURE_CROSS_ORIGIN_OPENER_POLICY = os.environ.get("DJANGO_SECURE_CROSS_ORIGIN_OPENER_POLICY")
SECURE_SSL_REDIRECT = True if os.environ.get("DJANGO_SECURE_SSL_REDIRECT") == "TRUE" else False

# ================================================================
# LOGGING
# ================================================================
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_DIR = os.environ.get("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} - {message}",
            "style": "{",
        },
        "simple": {
            "format": "[{levelname}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "app.log"),
            "formatter": "verbose",
        },
        "error_file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "error.log"),
            "level": "ERROR",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file", "error_file"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file", "error_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "file", "error_file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# ================================================================
# DJANGO APPS
# ================================================================
INSTALLED_APPS = [
    # Django built-in apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "widget_tweaks",
    "django_celery_beat",
    # Local apps
    "apps.common",
    "apps.converter",
    "apps.dashboard",
    "apps.account",
    "apps.institutional",
    "apps.billing",
    "apps.notification",
]

# ================================================================
# MIDDLEWARE
# ================================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ================================================================
# URLS & WSGI
# ================================================================
ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

# ================================================================
# TEMPLATES
# ================================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.billing.context_processors.user_balance",
            ],
        },
    },
]

# ================================================================
# DATABASES
# ================================================================

DATABASES = {
    "default": {
        "ENGINE": f"django.db.backends.{os.getenv('DB_ENGINE')}",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}

if "test" in sys.argv:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

# ================================================================
# AUTHENTICATION & PASSWORD VALIDATION
# ================================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_USER_MODEL = "user_account.User"

ACCOUNT_FORMS = {
    "login": "apps.account.forms.CustomLoginForm",
}

LOGIN_URL = "apps.account:login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# ================================================================
# INTERNATIONALIZATION & TIMEZONE
# ================================================================
USE_TZ = True
USE_I18N = True

TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "America/Recife")
LANGUAGE_CODE = os.environ.get("DJANGO_LANGUAGE_CODE", "pt-BR")

LANGUAGES = (
    ("pt-br", "Português"),
    ("en", "English"),
)

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# ================================================================
# STATIC & MEDIA FILES
# ================================================================
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STATIC_URL = "static/"
STATIC_ROOT = os.environ.get("DJANGO_STATIC_ROOT", "/usr/share/nginx/html")

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# ================================================================
# CELERY CONFIGURATION
# ================================================================
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = None

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

CELERY_TIMEZONE = "America/Sao_Paulo"
CELERY_TRACK_STARTED = True
CELERY_IGNORE_RESULT = False

CELERY_BEAT_SCHEDULE = {
    "delete-expired-urls-every-hour": {
        "task": "apps.converter.tasks.delete_expired_urls",
        "schedule": crontab(minute=0, hour="*"),
    },
    "disable-expired-subscriptions-daily": {
        "task": "apps.billing.tasks.disable_user_subscription",
        "schedule": crontab(minute=0, hour=0),
    },
}

MERCADO_PAGO_ACCESS_TOKEN = os.environ.get("MERCADO_PAGO_ACCESS_TOKEN", "")
MERCADO_PAGO_PUBLIC_KEY = os.environ.get("MERCADO_PAGO_PUBLIC_KEY", "")
MERCADO_PAGO_WEBHOOK_SECRET = os.environ.get("MERCADO_PAGO_WEBHOOK_SECRET", "")

# ================================================================
# EMAIL CONFIGURATION
# ================================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

try:
    EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST")
    EMAIL_PORT = int(os.environ.get("DJANGO_EMAIL_PORT", 465))
    EMAIL_USE_SSL = os.environ.get("DJANGO_EMAIL_USE_SSL", "").lower() in ["true", "1", "yes"]
    EMAIL_USE_TLS = os.environ.get("DJANGO_EMAIL_USE_TLS", "").lower() in ["true", "1", "yes"]
    EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_HOST_PASSWORD")
    DEFAULT_FROM_EMAIL = os.environ.get("DJANGO_DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

except KeyError as e:
    missing_key = e.args[0]
    raise RuntimeError(
        f"Configuração de e-mail ausente: a variável de ambiente '{missing_key}' não foi definida."
    )

except ValueError as e:
    raise RuntimeError(f"Erro na configuração de e-mail: {e}")
