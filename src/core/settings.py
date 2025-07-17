import os
from pathlib import Path
from dotenv import load_dotenv as loadenv

BASE_DIR = Path(__file__).resolve().parent.parent

env_file = os.environ.get('DJANGO_ENV_FILE')

if not env_file:
    loadenv(dotenv_path=BASE_DIR / 'prod.env')
loadenv(dotenv_path=env_file)

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DEBUG = True if os.environ.get('DJANGO_DEBUG') == 'TRUE' else False

ALLOWED_HOSTS = [host for host in os.environ.get(
    'DJANGO_ALLOWED_HOSTS', '').split(',') if host]

CSRF_TRUSTED_ORIGINS = [origin for origin in os.environ.get(
    'DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if origin]

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


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',

    'apps.converter',
    'apps.account'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

SECURE_CROSS_ORIGIN_OPENER_POLICY = os.environ.get(
    'DJANGO_SECURE_CROSS_ORIGIN_OPENER_POLICY')

SECURE_SSL_REDIRECT = True if os.environ.get(
    'DJANGO_SECURE_SSL_REDIRECT') == 'TRUE' else False

APPEND_SLASH = True
ROOT_URLCONF = 'core.urls'

SITE_ID = int(os.environ.get('DJANGO_SITE_ID', 1))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'core.wsgi.application'


if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DB_USER = os.getenv('DB_USER', '')
    DB_NAME = os.getenv('DB_NAME', '')
    DB_HOST = os.getenv('DB_HOST', '')
    DB_PORT = os.getenv('DB_PORT', '')
    DB_ENGINE = os.getenv('DB_ENGINE', '')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.' + DB_ENGINE,
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


USE_TZ = True
USE_I18N = True

TIME_ZONE = os.environ.get('DJANGO_TIME_ZONE', 'America/Recife')
LANGUAGE_CODE = os.environ.get('DJANGO_LANGUAGE_CODE', 'pt-BR')

LANGUAGES = (
    ('pt-br', 'Português'),
    ('en', 'English'),
)

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATIC_URL = 'static/'
STATIC_ROOT = os.environ.get('DJANGO_STATIC_ROOT', '/usr/share/nginx/html')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

ACCOUNT_FORMS = {
    'login': 'apps.account.forms.CustomLoginForm',
}
