import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, '/home/fofofish/fofofish')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fofofish.settings')

# Check if Django is already initialized to prevent reentrant errors
from django.apps import apps as django_apps

if not django_apps.ready:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
else:
    # Django is already initialized, use NullApplication
    def application(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [b'Django app already initialized']
