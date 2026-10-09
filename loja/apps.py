from django.apps import AppConfig


class LojaConfig(AppConfig):
    name = 'loja'
    def ready(self):
        from . import signals 
