from django.apps import AppConfig


class DatasetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.datasets'
    verbose_name = 'Datasets'
    
    def ready(self):
        import apps.datasets.signals
