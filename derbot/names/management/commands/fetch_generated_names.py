from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from derbot.names.tasks import fetch_generated_name

logger = settings.LOGGER


class Command(BaseCommand):
    help = "Fetches generated names from the API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--number", "-n", type=int, help="Number of names to fetch", default=1
        )

    def handle(self, *args, **options):
        try:
            number = options["number"]
            logger.info(f"Fetching {number} generated name(s) from the API")
            for i in range(number):
                fetch_generated_name.delay()
        except Exception as e:
            raise CommandError(e)
