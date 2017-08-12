# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import json

from rest_framework import viewsets
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder

from taggit.models import Tag

from crime import settings
from reports.models import Incident, Comment, Station
from reports import atom_scraper
from reports.serializers import (UserSerializer, StationSerializer,
                                 IncidentSerializer, CommentSerializer)


def do_scrape_atom(request):
    if request.GET.get('trigger') != settings.get_secret('TRIGGER_KEY'):
        return HttpResponse('go away')
    atom_scraper.scrape()
    return HttpResponse('done scraping')


def home(request):
    return listing(request, datetime.datetime.now())


def about(request):
    return render(request, 'about.html')


def incidents_for_date(request, year, month, day):
    return listing(request, datetime.date(int(year), int(month), int(day)))


def listing(request, date):
    valid_dates = list()
    for dateobj in Incident.objects.values('incident_date').distinct():
        valid_dates.append(dateobj['incident_date'].strftime('%Y-%m-%d'))
    valid_dates = json.dumps(valid_dates)
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
        'valid_dates': valid_dates,
    })


def single_incident(request, incident_id):
    incident = get_object_or_404(Incident, pk=incident_id)
    if request.method == 'POST':
        Comment.objects.create(
            incident=incident, text=request.POST.get('comment'))
        return redirect('incident', incident_id=incident_id)
    return render(request, 'incident.html', {'incident': incident})


def view_station(request, station_id):
    station = get_object_or_404(Station, abbreviation=station_id)
    incidents = Incident.objects.filter(
        station__id=station.id,
    ).order_by('-incident_dt')
    incidents_count = len(incidents)
    paginator = Paginator(incidents, 25)

    page = request.GET.get('page')
    try:
        incidents = paginator.page(page)
    except PageNotAnInteger:
        incidents = paginator.page(1)
    except EmptyPage:
        incidents = paginator.page(paginator.num_pages)

    return render(request, 'station.html', {'station': station,
                  'incidents': incidents, 'incidents_count': incidents_count})


def tag(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    incidents = Incident.objects.filter(
        tags__id=tag.id,
    ).order_by('-incident_dt')
    incidents_count = len(incidents)
    paginator = Paginator(incidents, 25)

    page = request.GET.get('page')
    try:
        incidents = paginator.page(page)
    except PageNotAnInteger:
        incidents = paginator.page(1)
    except EmptyPage:
        incidents = paginator.page(paginator.num_pages)

    return render(request, 'tag.html', {'tag': tag, 'incidents': incidents,
                  'incidents_count': incidents_count})


# pylint: disable=too-many-ancestors
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
