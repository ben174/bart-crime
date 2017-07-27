# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime

from crime import settings
from reports.models import Report, Incident, Comment
from reports import scraper

from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def report_webhook(request):
    if request.GET.get('trigger') != settings.get_secret('TRIGGER_KEY'):
        return HttpResponse('go away')
    report = Report.objects.create(body=request.body)
    report.create_incidents()
    return HttpResponse('incident created')

def do_scrape(request):
    scraper.scrape()
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
