# coding: utf-8
from django.conf.urls import url, include
from app import views

urlpatterns = [
    url('^accounts/', include('django.contrib.auth.urls')),
    url(r'^annc/(?P<name>.+)/$', views.annc, name='annc'), 
    url(r'^sanban/(?P<name>\d+)/$', views.sanban, name='sanban'),
    url(r'^test/$', views.test, name='test'),
    url(r'^news/$', views.news, name='news'),
    url(r'^add/', views.add, name='add'),
    url(r'^index/$', views.index, name='index'),
    url(r'^finance/$', views.finance, name='finance'),
    url(r'^companyfinance/$', views.companyfinance, name='companyfinance'),
    url(r'^investor/$', views.investor, name='investor'),
    url(r'^thinktank/$', views.thinktank, name='thinktank'),
    url(r'^thinktankdetail/$', views.thinktankdetail, name='thinktankdetail'),
    url(r'^login/$', views.login, name='login'),
    #url(r'^news/(?P<name>(news)?\d+)/$', views.news, name='news'),
    url(r'^project/(?P<pk>[1-9]\d*)/$', views.project, name='project'),
    url(r'^userinfofinance/$', views.userinfofinance, name='userinfofinance'),

    url(r'^join/$', views.join, name='join'),
]
