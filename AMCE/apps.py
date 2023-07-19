from django.apps import AppConfig


class AmceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'AMCE'

    def ready(self):
    	import AMCE.signals