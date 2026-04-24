import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production-xyz123')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'corsheaders',
    'profiles',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'insighta_labs.urls'

DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'
    )
}

# For PostgreSQL (recommended for production), use:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get('DB_NAME', 'insighta'),
#         'USER': os.environ.get('DB_USER', 'postgres'),
#         'PASSWORD': os.environ.get('DB_PASSWORD', ''),
#         'HOST': os.environ.get('DB_HOST', 'localhost'),
#         'PORT': os.environ.get('DB_PORT', '5432'),
#     }
# }

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'EXCEPTION_HANDLER': 'profiles.exceptions.custom_exception_handler',
}

# CORS — allow all origins as required by the grading script
CORS_ALLOW_ALL_ORIGINS = True
CORS_URLS_REGEX = r'^/api/.*$'
WSGI_APPLICATION = 'insighta_labs.wsgi.application'
