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

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'stations', views.StationViewSet)
router.register(r'reports', views.ReportViewSet)
router.register(r'incidents', views.IncidentViewSet)
router.register(r'comments', views.CommentViewSet)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^report/', views.report_webhook),
    url(r'^about/', views.about),
    url(r'^incident/(?P<incident_id>[0-9]+)/', views.incident, name='incident'),
    url(r'^date/(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})/', views.date),
    url(r'^scrape/', views.do_scrape),
    url(r'^mailgun/', views.handle_mailgun_webhook),
    url(r'^$', views.home),
    url(r'^api/v0/', include(router.urls)),
]
