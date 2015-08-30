"""
Django settings for django-jquery-file-upload project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""
import redis
import os
# from redis_sessions_fork.session import SessionStore

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
BASE_ABS_DIR = os.path.abspath(os.path.dirname(__file__))
os.environ['CLOUDCV_ABS_DIR'] = BASE_ABS_DIR

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '9%$in^gpdaig@v3or_to&_z(=n)3)$f1mr3hf9e#kespy2ajlo'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

SITE_ID = 3

INSTALLED_APPS = (
	'app',
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.sites',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'rest_framework',
	'allauth',
	'allauth.account',
	'allauth.socialaccount',
	'allauth.socialaccount.providers.google',
	'allauth.socialaccount.providers.dropbox',
	'redis_sessions_fork',
	'organizations',

)

MIDDLEWARE_CLASSES = (
	'django.contrib.sessions.middleware.SessionMiddleware',
	# 'cloudcv17.settings.CustomSessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

STATICFILES_FINDERS = (
	"django.contrib.staticfiles.finders.FileSystemFinder",
	"django.contrib.staticfiles.finders.AppDirectoriesFinder",
)
ROOT_URLCONF = 'cloudcv17.urls'

WSGI_APPLICATION = 'cloudcv17.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.sqlite3',
		'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
	}
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

# STATIC_ROOT = os.path.abspath(os.path.dirname(__file__)) +'/static/'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.abspath(os.path.dirname(__file__)) + '/media/'
"""
LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'formatters': {
		'verbose': {
			'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
			'datefmt' : "%d/%b/%Y %H:%M:%S"
		},
		'simple': {
			'format': '%(levelname)s %(message)s'
		},
	},
	'handlers': {
		'file': {
			'level': 'DEBUG',
			'class': 'logging.FileHandler',
			'filename': 'mysite.log',
			'formatter': 'verbose'
		},
	},
	'loggers': {
		'django': {
			'handlers':['file'],
			'propagate': True,
			'level':'DEBUG',
		},
		'app': {
			'handlers': ['file'],
			'level': 'DEBUG',
		},
	}
}

"""
r = redis.StrictRedis(host='redis', port=6379, db=0)
r.set('CLOUDCV_ABS_DIR', BASE_ABS_DIR)
r.set('CLOUDCV_MEDIA_ROOT', MEDIA_ROOT)
r.set('CLOUDCV_PIC_ROOT', os.path.join(MEDIA_ROOT, 'pictures', 'cloudcv'))

# Global settings for REST framework API are kept in a single configuration dictionary 
REST_FRAMEWORK = {
	'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.AllowAny',),
	'DEFAULT_RENDERER_CLASSES': (
		'rest_framework.renderers.JSONRenderer',
		'rest_framework.renderers.BrowsableAPIRenderer',
	),
	'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
}

TEMPLATE_CONTEXT_PROCESSORS = (
	"django.core.context_processors.media",
	"django.core.context_processors.static",
	"django.contrib.auth.context_processors.auth",
	"django.core.context_processors.request",
	"allauth.account.context_processors.account",
	"allauth.socialaccount.context_processors.socialaccount",
	# "django.core.context_processors.debug",
	# "django.core.context_processors.i18n",
	# "django.contrib.messages.context_processors.messages",
	# "allauth.context_processors.allauth",
)

# If running Django 1.8+, specify the context processors
# as follows:
# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 # Already defined Django-related contexts here
#                 # `allauth` needs this from django
#                 'django.core.context_processors.request',
#                 # `allauth` specific context processors
#                 'allauth.account.context_processors.account',
#                 'allauth.socialaccount.context_processors.socialaccount',
#             ],
#         },
#     },
# ]

AUTHENTICATION_BACKENDS = (
	'django.contrib.auth.backends.ModelBackend',
	'allauth.account.auth_backends.AuthenticationBackend',
)

LOGIN_REDIRECT_URL = "/workspace"

LOGIN_URL = "/login"

LOGOUT_URL = "/logout"

ACCOUNT_EMAIL_REQUIRED = True

# for authentication using both Username or Email
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'

#Setting the SMTP Configuration for sending the mails to cloudcv users

# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# EMAIL_USE_TLS = True
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# # EMAIL_HOST_USER = 'youremail@gmail.com'
# EMAIL_HOST_PASSWORD = 'password'


ACCOUNT_AUTHENTICATION_METHOD = 'username_email'

DROPBOX_APP_KEY = "random string"
DROPBOX_APP_SECRET = "random string"

GOOGLE_APP_CREDENTIALS = {"web":
	{"client_id":"89054035800-j4v3r4l2nfmqjipd5grmv5b4jo0.apps.googleusercontent.com",
	"auth_uri":"https://accounts.google.com/o/oauth/auth",
	"token_uri":"https://accounts.google.com/o/oauth2/token",
	"auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
	"client_email":"",
	"client_x509_cert_url":"",
	"client_secret":"e7gyq39-K7iraVO4ZovpfjP",
	"redirect_uris":["http://localhost:8000/googlelogin/callback/"],
	"javascript_origins":["http://localhost:8080"]
	}
}

SESSION_ENGINE = 'redis_sessions_fork.session'

# all these options are defaults, you can skip anyone
SESSION_REDIS_HOST = 'redis'
SESSION_REDIS_PORT = 6379
SESSION_REDIS_DB = 0
SESSION_REDIS_PASSWORD = None
SESSION_REDIS_PREFIX = None
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

