import datetime

from django.core.management.base import BaseCommand, CommandError

from reports import scraper


class Command(BaseCommand):
    help = 'Create incidents from reports'


    def handle(self, *args, **options):
        scraper.scrape()
        self.stdout.write(self.style.SUCCESS('Successfully created incidents.'))
