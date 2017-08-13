from reports.models import Station


def station_list(request):  # pylint: disable=unused-argument
    stations = list()
    for station in Station.objects.all():
        station.incidents_count = station.incidents.count()
        stations.append(station)
    return {'station_list': stations}
