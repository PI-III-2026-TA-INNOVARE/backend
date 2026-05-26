from pathlib import Path
from decouple import config
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
INSTITUTIONAL_DOMAINS_FILE = BASE_DIR / 'data' / 'world_universities_and_domains.json'

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    
    'apps.researchers',
    'apps.companies',
    'apps.educations',
    'apps.experiences',
    'apps.resumes',
    'apps.skills',
    'apps.universities',
    'apps.research',
    'apps.research_candidates',
    'apps.search',
    'apps.research_area',
    'apps.users',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', 
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",  
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'USER_ID_FIELD': 'id_user',
    'USER_ID_CLAIM': 'user_id',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'P&D Connect API',
    'DESCRIPTION': 'API para conexão entre pesquisadores e empresas',
    'VERSION': '1.0.0',
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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'
SEARCH_EMBEDDING_DIMENSION = config('SEARCH_EMBEDDING_DIMENSION', default=384, cast=int)
SEARCH_EMBEDDING_MODEL = config(
    'SEARCH_EMBEDDING_MODEL',
    default='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
)
SEARCH_EMBEDDING_ALLOW_HASH_FALLBACK = config(
    'SEARCH_EMBEDDING_ALLOW_HASH_FALLBACK',
    default=True,
    cast=bool,
)
SEARCH_MIN_HYBRID_SCORE = config('SEARCH_MIN_HYBRID_SCORE', default=0.24, cast=float)
SEARCH_RELATIVE_CUTOFF = config('SEARCH_RELATIVE_CUTOFF', default=0.55, cast=float)
AI_MATCH_LIMIT_PER_RESEARCH = config('AI_MATCH_LIMIT_PER_RESEARCH', default=30, cast=int)
AI_MATCH_LIMIT_PER_RESEARCHER = config('AI_MATCH_LIMIT_PER_RESEARCHER', default=30, cast=int)
AI_MATCH_MIN_SCORE = config('AI_MATCH_MIN_SCORE', default=0.26, cast=float)
AI_MATCH_WEIGHT_SEMANTIC = config('AI_MATCH_WEIGHT_SEMANTIC', default=0.45, cast=float)
AI_MATCH_WEIGHT_LEXICAL = config('AI_MATCH_WEIGHT_LEXICAL', default=0.20, cast=float)
AI_MATCH_WEIGHT_AREA = config('AI_MATCH_WEIGHT_AREA', default=0.25, cast=float)
AI_MATCH_WEIGHT_AVAILABILITY = config('AI_MATCH_WEIGHT_AVAILABILITY', default=0.10, cast=float)
AI_MATCH_RECOMMENDATION_MIN_SCORE = config('AI_MATCH_RECOMMENDATION_MIN_SCORE', default=0.30, cast=float)
AI_MATCH_REQUIRE_STRONG_REASON = config('AI_MATCH_REQUIRE_STRONG_REASON', default=True, cast=bool)
AI_MATCH_ASYNC_ENABLED = config('AI_MATCH_ASYNC_ENABLED', default=False, cast=bool)

CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = config('CELERY_TASK_TIME_LIMIT', default=900, cast=int)
CELERY_TASK_SOFT_TIME_LIMIT = config('CELERY_TASK_SOFT_TIME_LIMIT', default=840, cast=int)

STATIC_URL = 'static/'

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@pdconnect.com')

# Frontend URL for password reset link
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:5173')
