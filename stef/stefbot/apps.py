from django.apps import AppConfig

class StefbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stefbot'

    def ready(self):
        import stefbot.signals  # Подключаем сигналы
