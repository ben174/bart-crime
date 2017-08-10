# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime

from rest_framework import viewsets
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt

from crime import settings
from reports.models import Incident, Comment, Station
from reports import atom_scraper
from reports.serializers import (UserSerializer, StationSerializer,
                                 IncidentSerializer, CommentSerializer)


def do_scrape_atom(request):
    return
    if request.GET.get('trigger') != settings.get_secret('TRIGGER_KEY'):
        return HttpResponse('go away')
    atom_scraper.scrape()
    return HttpResponse('done scraping')

def home(request):
    date = datetime.datetime.now()
    return listing(request, date)

def about(request):
    return render(request, 'about.html')

def date(request, year, month, day):
    date = datetime.date(int(year), int(month), int(day))
    return listing(request, date)

def listing(request, date):
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    curr_date = Incident.objects.filter(
        incident_date__lte=date,
    ).latest('incident_dt').incident_date
    try:
        next_date = Incident.objects.filter(
            incident_date__gt=curr_date,
            incident_date__lt=tomorrow,
        ).earliest('incident_dt').incident_date
    except Incident.DoesNotExist:
        next_date = None
    try:
        prev_date = Incident.objects.filter(
            incident_date__lt=curr_date,
        ).latest('incident_dt').incident_date
    except Incident.DoesNotExist:
        prev_date = None
    incidents = Incident.objects.filter(
        incident_dt__isnull=False,
        incident_date=curr_date,
    ).order_by('-incident_dt')
    return render(request, 'home.html', {
        'curr_date': curr_date,
        'incidents': incidents,
        'prev_date': prev_date,
        'next_date': next_date,
    })

def incident(request, incident_id):
    incident = get_object_or_404(Incident, pk=incident_id)
    if request.method == 'POST':
        Comment.objects.create(incident=incident, text=request.POST.get('comment'))
        return redirect('incident', incident_id=incident_id)
    return render(request, 'incident.html', {'incident': incident})

def station(request, station_id):
    station = get_object_or_404(Station, abbreviation=station_id)
    return render(request, 'station.html', {'station': station})

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

class StationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows stations to be viewed
    """
    queryset = Station.objects.all().order_by('-abbreviation')
    serializer_class = StationSerializer

class IncidentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows incidents to be viewed
    """
    queryset = Incident.objects.all().order_by('-incident_dt')
    serializer_class = IncidentSerializer

class CommentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows comments to be viewed
    """
    queryset = Comment.objects.all().order_by('-created_dt')
    serializer_class = CommentSerializer
