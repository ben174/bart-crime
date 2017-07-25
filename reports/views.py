# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from reports.models import Report

from django.shortcuts import render

def report_webhook(request):
    #TODO: authenticate via secret
    report = Report.objects.create(body=request.text)
