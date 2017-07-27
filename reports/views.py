# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime

from crime import settings
from reports.models import Report, Incident
from reports import scraper

from django.shortcuts import render, get_object_or_404

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def report_webhook(request):
    if request.GET.get('trigger') != settings.get_secret('TRIGGER_KEY'):
        return None
    report = Report.objects.create(body=request.body)
    report.create_incidents()

def do_scrape(request):
    if request.GET.get('trigger') != settings.get_secret('TRIGGER_KEY'):
        return None
    scraper.scrape()

def home(request):
    date = datetime.datetime.now()
    return listing(request, date)

def date(request, year, month, day):
    date = datetime.date(int(year), int(month), int(day))
    return listing(request, date)

def listing(request, date):
    next_date = date + datetime.timedelta(days=-1)
    current_date = Incident.objects.filter(
        incident_dt__isnull=False,
        incident_dt__lte=next_date,
    ).latest('incident_dt').incident_date
    prev_date = Incident.objects.filter(
        incident_dt__isnull=False,
        incident_dt__lt=current_date,
    ).latest('incident_dt').incident_date
    incidents = Incident.objects.filter(
        incident_dt__isnull=False,
        incident_date=current_date,
    ).order_by('-incident_dt')
    return render(request, 'home.html', {
        'current_date': current_date,
        'incidents': incidents,
        'prev_date': prev_date
    })

def incident(request, incident_id):
    incident = get_object_or_404(Incident, pk=incident_id)
    return render(request, 'incident.html', {'incident': incident})
