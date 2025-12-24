import os
from fofofish import application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fofofish.settings')
application = get_wsgi_application()
