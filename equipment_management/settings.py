"""
Django settings for equipment_management project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Try to import decouple for environment variables
try:
    from decouple import config
    USE_DECOUPLE = True
except ImportError:
    USE_DECOUPLE = False
    def config(key, default=None, cast=None):
        return default

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-equipment-management-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',') if config('ALLOWED_HOSTS', default='') else []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'corsheaders',
    # Apps
    'equipment',
    'tickets',
    'renewals',
    'nas_management',
    'api',  # REST API for mobile app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware - phải đặt trước CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'equipment_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'equipment_management.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'vi'

TIME_ZONE = 'Asia/Ho_Chi_Minh'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# CORS settings - cho phép mobile app truy cập API
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:3000",  # React Native debugger
]

# Cho phép credentials (cookies, session)
CORS_ALLOW_CREDENTIALS = True

# Cho phép tất cả headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Trong development, có thể cho phép tất cả origins (KHÔNG dùng trong production!)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

# LDAP Authentication Settings
LDAP_SERVER = config('LDAP_SERVER', default='192.168.104.80')
LDAP_DOMAIN = config('LDAP_DOMAIN', default='pegaholdings.local')
LDAP_PORT = config('LDAP_PORT', default=389, cast=int)
LDAP_USE_SSL = config('LDAP_USE_SSL', default=False, cast=bool)

# LDAP Base DN - tự động tạo từ domain
LDAP_BASE_DN = config('LDAP_BASE_DN', default='DC=pegaholdings,DC=local')
LDAP_SEARCH_DN = config('LDAP_SEARCH_DN', default=f'CN=Users,{LDAP_BASE_DN}')

# LDAP Service Account (optional - nếu cần để search users)
# Nếu không có, sẽ dùng anonymous bind
LDAP_SERVICE_DN = config('LDAP_SERVICE_DN', default=None)
LDAP_SERVICE_PASSWORD = config('LDAP_SERVICE_PASSWORD', default=None)

# LDAP Search User (alternative - dùng một user account để search)
# Format: chỉ cần username, không cần domain
LDAP_SEARCH_USER = config('LDAP_SEARCH_USER', default='p.huy.nn')
LDAP_SEARCH_USER_PASSWORD = config('LDAP_SEARCH_USER_PASSWORD', default='Pega@2025')

# Authentication Backends - LDAP trước, sau đó Django default
AUTHENTICATION_BACKENDS = [
    'equipment.ldap_backend.LDAPBackend',  # LDAP authentication
    'django.contrib.auth.backends.ModelBackend',  # Django default (fallback)
]

# Login settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
