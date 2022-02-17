from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from derbot.names.models import DerbyName
from derbot.names.tasks import generate_tank

logger = settings.LOGGER


@receiver(post_save, sender=DerbyName)
def generate_missing_tank(sender, instance, created, **kwargs):
    if instance.cleared and not instance.jersey:
        logger.info(f"{sender}: Generating missing tank for {instance.name}")
        generate_tank.delay(instance.id)
