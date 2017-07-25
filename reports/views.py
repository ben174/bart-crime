# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from reports.models import Report

from django.shortcuts import render

def report_webhook(request):
    #TODO: authenticate via secret
    from django.contrib.auth.models import User
    User.objects.create_superuser(username='admin', password='changeme', email='admin@admin.com')

    report = Report.objects.create(body=request.content)
