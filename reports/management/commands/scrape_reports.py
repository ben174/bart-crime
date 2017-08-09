import datetime

from django.core.management.base import BaseCommand, CommandError

from reports import mail_scraper


class Command(BaseCommand):
    help = 'Create incidents from reports'


    def handle(self, *args, **options):
        mail_scraper.scrape()
        self.stdout.write(self.style.SUCCESS('Successfully created incidents.'))
