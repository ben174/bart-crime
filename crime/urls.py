"""crime URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

from reports import views

from rest_framework import routers

API = routers.DefaultRouter()
API.register(r'users', views.UserViewSet)
API.register(r'stations', views.StationViewSet)
API.register(r'incidents', views.IncidentViewSet)
API.register(r'comments', views.CommentViewSet)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^about/', views.about),
    url(r'^incident/(?P<incident_id>[0-9]+)/',
        views.single_incident, name='incident'),
    url(r'^date/(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})/',
        views.incidents_for_date),
    url(r'^station/(?P<station_id>[\w]+)/', views.view_station,
        name='station'),
    url(r'^scrape/atom/', views.do_scrape_atom),
    url(r'^$', views.home),
    url(r'^api/v0/', include(API.urls)),
]
