"""
Django settings for netguard_core project.
"""

from pathlib import Path
import os

# ─── Optional .env loader ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    # override=True ensures .env beats any stale environment variables
    load_dotenv(BASE_DIR / '.env', override=True)
except ImportError:
    # python-dotenv not installed; environment variables should be set elsewhere
    pass


# ─── Security ─────────────────────────────────────────────────────────────────
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'CHANGE-ME-in-production')
if not DEBUG and SECRET_KEY == 'CHANGE-ME-in-production':
    raise RuntimeError('Set DJANGO_SECRET_KEY in the production environment.')

ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if host.strip()]
vercel_host = os.getenv('VERCEL_URL', '').strip()
if vercel_host:
    ALLOWED_HOSTS.append(vercel_host)

CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']
if vercel_host:
    CSRF_TRUSTED_ORIGINS.append(f'https://{vercel_host}')
CSRF_TRUSTED_ORIGINS.extend(
    origin.strip() for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()
)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# ─── Application definition ───────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'scanner',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'netguard_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Add project-level templates dir so login.html is found
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

WSGI_APPLICATION = 'netguard_core.wsgi.application'


# ─── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
if DATABASE_URL:
    import dj_database_url
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=not DEBUG)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ─── Password validation ──────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ─── Internationalisation ─────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ─── Static files ─────────────────────────────────────────────────────────────
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'scanner' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'


# ─── Auth redirects ───────────────────────────────────────────────────────────
# Where @login_required sends unauthenticated users
LOGIN_URL = '/login/'
# Where Django redirects after a successful login (your dashboard)
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'


