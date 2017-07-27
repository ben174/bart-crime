# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime

from crime import settings
from reports.models import Report, Incident
from reports import scraper

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def report_webhook(request):
    #TODO: authenticate via secret
    if request.GET.get('trigger') != settings.get_secret('TRIGGER_KEY'):
        return None
    report = Report.objects.create(body=request.body)
    report.create_incidents()

def do_scrape(request):
    if request.GET.get('trigger') != settings.get_secret('TRIGGER_KEY'):
        return None
    scraper.scrape()

def home(request):
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=-1)
    latest_date = Incident.objects.filter(
        incident_dt__isnull=False,
        incident_dt__lte=tomorrow
    ).latest('incident_dt').incident_date
    incidents = Incident.objects.filter(incident_dt__isnull=False, incident_date=latest_date).order_by('-incident_dt')
    return render(request, 'home.html', {'incidents': incidents})
