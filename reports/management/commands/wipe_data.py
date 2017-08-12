from django.core.management.base import BaseCommand
from reports.models import Incident


class Command(BaseCommand):
    help = 'Delete all reports and incidents'

    def handle(self, *args, **options):
        Incident.objects.all().delete()
