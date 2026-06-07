from django.apps import AppConfig


class ClassesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'classes'
    verbose_name = 'Online Classes'


    def ready(self):
        try:
            import classes.signals  # noqa
        except ImportError:
            pass
