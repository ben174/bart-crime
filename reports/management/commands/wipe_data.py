from django.core.management.base import BaseCommand, CommandError
from reports.models import Report, Incident

class Command(BaseCommand):
    help = 'Delete all reports and incidents'

    def handle(self, *args, **options):
        Incident.objects.all().delete()
        Report.objects.all().delete()
