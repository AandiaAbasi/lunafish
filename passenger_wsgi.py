import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, '/home/fofofish/fofofish')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fofofish.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
