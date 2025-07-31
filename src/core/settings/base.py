import os
from pathlib import Path
from dotenv import load_dotenv

# =================================
# === Load Enviroment Variables ===
# =================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_file = os.environ.get('DJANGO_ENV_FILE', BASE_DIR / 'dev.env')
load_dotenv(dotenv_path=env_file)

# ============================
# === Django Base Settings ===
# ============================
def env_bool(var_name, default='FALSE'):
    return os.getenv(var_name, default).strip().upper() == 'TRUE'

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DEBUG = env_bool('DJANGO_DEBUG')

ALLOWED_HOSTS = [host for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if host]
CSRF_TRUSTED_ORIGINS = [origin for origin in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if origin]

ROOT_URLCONF = 'core.urls'
WSGI_APPLICATION = 'core.wsgi.application'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SITE_ID = 1
APPEND_SLASH = True
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
SECURE_SSL_REDIRECT = False

# ========================
# === Logging Settings ===
# ========================
LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
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

# ====================
# === Applications ===
# ====================
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
    'apps.account',
]

# ===================
# === Middlewares ===
# ===================
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

# ==================
# === URL e WSGI ===
# ==================
ROOT_URLCONF = 'core.urls'
WSGI_APPLICATION = 'core.wsgi.application'

# =================
# === Templates ===
# =================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

# ========================
# === Database and ORM ===
# ========================
DATABASES = {}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===============================
# === Security and Validators ===
# ===============================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =========================================
# === Language and Internationalization ===
# =========================================
USE_I18N = True
USE_TZ = True
TIME_ZONE = os.getenv('DJANGO_TIME_ZONE', 'America/Recife')
LANGUAGE_CODE = os.getenv('DJANGO_LANGUAGE_CODE', 'pt-BR')
LANGUAGES = (('pt-br', 'Português'), ('en', 'English'))
LOCALE_PATHS = [BASE_DIR / 'locale']

# ==============================
# === Static files and Media === 
# ==============================
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATIC_URL = 'static/'
STATIC_ROOT = os.getenv('DJANGO_STATIC_ROOT', '/usr/share/nginx/html')
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / 'static']

# ===============================
# === Authentication Backends ===
# ===============================
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend'
]

ACCOUNT_FORMS = {
    'login': 'apps.account.forms.CustomLoginForm',
}
