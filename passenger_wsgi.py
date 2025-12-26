import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, '/home/fofofish/fofofish')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fofofish.settings')

# Check if Django is already initialized
import django
from django.apps import apps as django_apps

if not django_apps.ready:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
else:
    # Django already initialized, get the app from wsgi module directly
    from fofofish.wsgi import application
