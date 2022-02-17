from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from psycopg2 import connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logger = settings.LOGGER


class Command(BaseCommand):
    help = "Creates the initial database"

    def handle(self, *args, **options):
        try:
            logger.info("Starting db creation")

            dbname = settings.DATABASES["default"]["NAME"]
            user = settings.DATABASES["default"]["USER"]
            password = settings.DATABASES["default"]["PASSWORD"]
            host = settings.DATABASES["default"]["HOST"]

            logger.info(f"Connecting to {host} as {user}")
            con = None
            con = connect(dbname="postgres", user=user, host=host, password=password)
            con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = con.cursor()
            logger.info(f"Creating db {dbname}")
            cur.execute(f'CREATE DATABASE "{dbname}"')
            cur.close()
            con.close()

            logger.info("Database created")
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise CommandError(f"Error creating database: {e}")
