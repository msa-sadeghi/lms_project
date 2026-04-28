from .base import *

DEBUG = True

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')


# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
