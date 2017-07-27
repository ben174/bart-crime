from django.core.management.base import BaseCommand, CommandError
from reports.models import Report, Incident

class Command(BaseCommand):
    help = 'Create incidents from reports'

    def handle(self, *args, **options):
        reports = Report.objects.filter(processed=False)
        reports = Report.objects.exclude(body='')
        Incident.objects.all().delete()

        for report in reports:
            report.create_incidents()

        self.stdout.write(self.style.SUCCESS('Successfully created incidents.'))
