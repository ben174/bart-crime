# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from reports.models import Station, Report, Incident

from django.contrib import admin

class IncidentAdmin(admin.ModelAdmin):
    list_display = ('title', 'incident_dt', 'body', 'icon')
admin.site.register(Incident, IncidentAdmin)
admin.site.register([Station, Report])
