from asyncio.log import logger

from django.apps import AppConfig


class NamesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "derbot.names"

    def ready(self):
        import derbot.names.signals

        logger.info(f"Signals loaded: {derbot.names.signals}")
