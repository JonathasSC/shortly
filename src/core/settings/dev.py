from .base import *
import os

# ============================
# === Django Base Settings ===
# ============================
DEBUG = True
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-key")
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# ========================
# === Database and ORM ===
# ========================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ====================
# === Applications ===
# ====================
INSTALLED_APPS += [
    'debug_toolbar',
]

# ===============================
# === Security and Validators ===
# ===============================
INTERNAL_IPS = ['127.0.0.1']

# ===================
# === Middlewares ===
# ===================
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
