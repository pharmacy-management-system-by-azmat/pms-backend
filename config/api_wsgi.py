import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('DJANGO_URLCONF', 'config.api_urls')

from django.core.wsgi import get_wsgi_application
from django.conf import settings

settings.ROOT_URLCONF = 'config.api_urls'
application = get_wsgi_application()