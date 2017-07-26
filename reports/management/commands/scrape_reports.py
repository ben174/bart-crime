import datetime

from django.core.management.base import BaseCommand, CommandError
import requests
from bs4 import BeautifulSoup

from reports.models import Report, Incident
from crime import settings


class Command(BaseCommand):
    help = 'Create incidents from reports'


    def handle(self, *args, **options):
        Report.objects.all().delete()
        Incident.objects.all().delete()
        inbox_url = '{}inbox?to={}&token={}'.format(
            settings.get_secret('MAIL_API_URL'),
            settings.get_secret('INBOX_NAME'),
            settings.get_secret('MAIL_TOKEN'),
        )
        inbox_data = requests.get(inbox_url).json()
        for message in inbox_data['messages']:
            if Report.objects.filter(email_id=message['id']).exists():
                print 'Skipping email: {}'.format(message['id'])
                continue

            print 'Downloading email: {}'.format(message['id'])
            email_url = '{}email?id={}&token={}'.format(
                settings.get_secret('MAIL_API_URL'),
                message['id'],
                settings.get_secret('MAIL_TOKEN'),
            )
            email_data = requests.get(email_url).json()
            email_html = email_data['data']['parts'][1]['body']
            report = Report.objects.create(
                report_dt=datetime.datetime.now()-datetime.timedelta(seconds=message['seconds_ago']),
                email_id=message['id'],
                body=email_html,
            )
            print 'Creating incidents...'
            report.create_incidents()

        self.stdout.write(self.style.SUCCESS('Successfully created incidents.'))
