"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

from config.fastapi_app import app as fastapi_app

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = fastapi_app
