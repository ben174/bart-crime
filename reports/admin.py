# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from reports.models import Station, Report, Incident

from django.contrib import admin

admin.site.register([Station, Report, Incident])
