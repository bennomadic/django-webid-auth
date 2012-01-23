from django.conf.urls.defaults import *
import views

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.tryme),
    url(r'^test/login$', views.test_login),
    url('^test/WebIDTest', views.webidlogin_report),
)
