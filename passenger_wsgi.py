import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, '/home/fofofish/fofofish')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fofofish.settings')

# Prevent reentrant django.setup() calls
if not django.apps.apps.ready:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
else:
    from fofofish.wsgi import application
