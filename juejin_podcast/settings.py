from datetime import timedelta
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-me-for-local-development')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('1', 'true', 'yes', 'on')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')
    if host.strip()
]


# Application definition

INSTALLED_APPS = [
    'simpleui',
    'corsheaders',
    'rest_framework',
    'accounts',
    'audios',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'juejin_podcast.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'audios.context_processors.admin_dashboard_stats',
            ],
        },
    },
]

WSGI_APPLICATION = 'juejin_podcast.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'music'),
        'USER': os.getenv('DB_USER', 'music'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'music'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'connect_timeout': 5,
            'read_timeout': 5,
            'write_timeout': 5,
        },
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

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:5174',
    'http://127.0.0.1:5174',
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:5174',
    'http://127.0.0.1:5174',
]

CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('Bearer',),
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

DJOSER = {
    'LOGIN_FIELD': 'username',
    'USER_CREATE_PASSWORD_RETYPE': False,
    'TOKEN_MODEL': None,
    'SERIALIZERS': {
        'user': 'accounts.serializers.UserSerializer',
        'current_user': 'accounts.serializers.CurrentUserSerializer',
    },
    'PERMISSIONS': {
        'user_create': ['rest_framework.permissions.IsAdminUser'],
        'user_delete': ['rest_framework.permissions.IsAdminUser'],
        'user_list': ['rest_framework.permissions.IsAdminUser'],
    },
}

ADMIN_DEFAULT_PASSWORD = os.getenv('ADMIN_DEFAULT_PASSWORD', 'change-this-default-password')

SIMPLEUI_HOME_TITLE = '掘金播客后台'
SIMPLEUI_HOME_ICON = 'fa fa-home'
SIMPLEUI_LOGO = ''
SIMPLEUI_HOME_INFO = False
SIMPLEUI_ANALYSIS = False
SIMPLEUI_STATIC_OFFLINE = True
SIMPLEUI_HOME_QUICK = False
SIMPLEUI_DEFAULT_THEME = 'simpleui.css'
SIMPLEUI_CONFIG = {
    'system_keep': False,
    'menu_display': ['账号管理', '音频管理'],
    'menus': [
        {
            'name': '账号管理',
            'icon': 'fas fa-users-cog',
            'models': [
                {
                    'name': '分组管理',
                    'icon': 'fas fa-layer-group',
                    'url': '/admin/accounts/managedgroup/',
                },
                {
                    'name': '账号管理',
                    'icon': 'fas fa-user',
                    'url': '/admin/accounts/manageduser/',
                },
            ],
        },
        {
            'name': '音频管理',
            'icon': 'fas fa-headphones',
            'models': [
                {
                    'name': '音频管理',
                    'icon': 'fas fa-file-audio',
                    'url': '/admin/audios/audio/',
                },
                {
                    'name': '音频清理',
                    'icon': 'fas fa-filter',
                    'url': '/admin/audios/audiocleanup/',
                },
                {
                    'name': '已听记录',
                    'icon': 'fas fa-clock-rotate-left',
                    'url': '/admin/audios/userlistened/',
                },
            ],
        },
    ],
}
SIMPLEUI_ICON = {
    '账号管理': 'fas fa-users-cog',
    'accounts': 'fas fa-users-cog',
    'accounts.ManagedUser': 'fas fa-user',
    'accounts.ManagedGroup': 'fas fa-layer-group',
    '音频管理': 'fas fa-headphones',
    'audios': 'fas fa-headphones',
    'audios.Audio': 'fas fa-file-audio',
    'audios.AudioCleanup': 'fas fa-filter',
    'audios.UserListened': 'fas fa-clock-rotate-left',
}
