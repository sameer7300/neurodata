from django.apps import AppConfig


class MlTrainingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ml_training'
    verbose_name = 'ML Training'
    
    def ready(self):
        import apps.ml_training.signals
