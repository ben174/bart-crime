import requests

from django.core.management.base import BaseCommand, CommandError
from reports.models import Station

class Command(BaseCommand):
    help = 'Import station data from the BART API'

    def handle(self, *args, **options):
        stations = requests.get('http://api.bart.gov/api/stn.aspx?cmd=stns&key=MW9S-E7SL-26DU-VV8V&json=y').json()
        for station in stations['root']['stations']['station']:
            if Station.objects.filter(abbreviation=station['abbr']).exists():
                print 'Skipping station: {} ({})'.format(station['name'],
                                                         station['abbr'])
                continue
            print 'Creating station: {} ({})'.format(station['name'],
                                                     station['abbr'])
            station['abbreviation'] = station.pop('abbr')
            station['latitude'] = station.pop('gtfs_latitude')
            station['longitude'] = station.pop('gtfs_longitude')
            Station.objects.create(**station).save()
