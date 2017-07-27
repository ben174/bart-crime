# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from reports.models import Report, Incident
from reports import scraper

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def report_webhook(request):
    #TODO: authenticate via secret
    report = Report.objects.create(body=request.body)
    report.create_incidents()

def do_scrape(request):
    scraper.scrape()

def home(request):
    return render(request, 'home.html', {'incidents': Incident.objects.all().order_by('-incident_dt')})
