from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from derbot.names.models import DerbyName, DerbyNumber
from derbot.names.tasks import generate_tank

logger = settings.LOGGER


@receiver(pre_save, sender=DerbyName)
def set_missing_number(sender, instance, *args, **kwargs):
    if not instance.registered and not instance.number:
        instance.number = DerbyNumber.objects.filter(cleared=True).order_by("?").first()


@receiver(post_save, sender=DerbyName)
def generate_missing_tank(sender, instance, *args, **kwargs):
    if instance.cleared and not instance.jersey:
        logger.info(f"{sender}: Generating missing tank for {instance.name}")
        generate_tank.delay(instance.id)
