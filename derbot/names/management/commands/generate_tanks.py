from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from derbot.names.models import DerbyName
from derbot.names.tasks import generate_tank

logger = settings.LOGGER


class Command(BaseCommand):
    help = 'Generates "tank" jersey(s) for name(s)'

    def add_arguments(self, parser):
        parser.set_defaults(overwrite=False)
        parser.add_argument("--overwrite", "-o", action="store_true")
        parser.add_argument("name_ids", nargs="*", type=int, default=None)

    def handle(self, *args, **options):
        try:
            if options["name_ids"]:
                logger.info(
                    f"Generating tanks for names: {options['name_ids']}; overwrite={options['overwrite']}"
                )
                name_ids = options["name_ids"]

            else:
                logger.info(
                    f"Generating tanks for all names; overwrite={options['overwrite']}"
                )
                if options["overwrite"]:
                    name_ids = DerbyName.objects.all().values_list("id", flat=True)
                else:
                    name_ids = DerbyName.objects.filter(jersey=None).values_list(
                        "id", flat=True
                    )
                # logger.debug(f"{len(name_ids)} names")
                # logger.debug(f"{name_ids}")
            for name_id in name_ids:
                generate_tank.delay(name_id, overwrite=options["overwrite"])
        except Exception as e:
            raise CommandError(e)
