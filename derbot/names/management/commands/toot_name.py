from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Exists, OuterRef, Q

from derbot.names.models import DerbyName, Toot
from derbot.names.tasks import toot_name

logger = settings.LOGGER


class Command(BaseCommand):
    help = "Toots specified name(s) - or random if none specified"

    def add_arguments(self, parser):
        parser.add_argument("name_ids", nargs="*", type=int, default=None)

    def handle(self, *args, **options):
        try:
            logger.info("Tooting names")
            logger.debug("Name IDs: %s", options["name_ids"])
            if options["name_ids"]:
                name_ids = options["name_ids"]
            else:
                name = (
                    DerbyName.objects.filter(
                        Q(registered=False)
                        & Q(cleared=True)
                        & ~Q(jersey=False)
                        & ~Q(Exists(Toot.objects.filter(name=OuterRef("pk"))))
                    )
                    .order_by("?")
                    .first()
                )
                logger.info(f"Toot name: {name}")
                name_ids = [name.id]
            if name_ids:
                for name_id in name_ids:
                    logger.info(f"Tooting name {name_id}")
                    toot_name.delay(name_id)
        except Exception as e:
            raise CommandError(e)
