from reports.models import Station, Incident

def station_list(request):
    stations = list()
    for station in Station.objects.all():
        station.incidents_count = station.incidents.count()
        stations.append(station)
    return {'station_list': stations}
