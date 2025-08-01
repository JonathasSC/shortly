from core.settings import base
import os

# ============================
# === Django Base Settings ===
# ============================
base.DEBUG = False
base.SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
base.ALLOWED_HOSTS = [host for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if host]

# ========================
# === Database and ORM ===
# ========================
base.DATABASES = {
    'default': {
        'ENGINE'  : 'django.db.backends.' + os.getenv('DB_ENGINE'),
        'NAME'    : os.getenv('DB_NAME', ''),
        'USER'    : os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST'    : os.getenv('DB_HOST', ''),
        'PORT'    : os.getenv('DB_PORT', ''),
    }
}

print(base.DATABASES)
