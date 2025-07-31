from src.core.settings import base
import os

# ============================
# === Django Base Settings ===
# ============================
base.DEBUG = True
base.SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-key")
base.ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# ========================
# === Database and ORM ===
# ========================
base.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': base.BASE_DIR / 'db.sqlite3',
    }
}

# ====================
# === Applications ===
# ====================
base.INSTALLED_APPS += [
    'debug_toolbar',
]

# ===============================
# === Security and Validators ===
# ===============================
INTERNAL_IPS = ['127.0.0.1']

# ===================
# === Middlewares ===
# ===================
base.MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
