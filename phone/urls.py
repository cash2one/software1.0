# coding: utf-8
from django.conf.urls import url
from phone import views

urlpatterns = [
    url(r'^test/$', views.test, name='test'),
    
    url(r'^openid/(?P<openid>.+)/$', views.openid, name='openid'),

    url(r'^sendcode/(?P<flag>[01])/(?P<weixin>[01])/$', views.sendcode, name='sendcode'),
    url(r'^registe/(?P<os>[12])/$', views.registe, name='registe'),
    url(r'^login/$', views.login_, name='login'),
    url(r'^resetpasswd/$', views.resetpasswd, name='resetpasswd'),
    url(r'^modifypasswd/$', views.modifypasswd, name='modifypasswd'),
    url(r'^logout/$', views.logout, name='logout'),

    url(r'^userinfo/$', views.userinfo, name='userinfo'),
    url(r'^leftslide/$', views.leftslide, name='leftslide'),
    url(r'^photo/$', views.photo, name='photo'),
    url(r'^bg/$', views.bg, name='bg'),
    url(r'^nickname/$', views.nickname, name='nickname'),
    url(r'^company/$', views.company, name='company'),
    url(r'^position/$', views.position, name='position'),
    url(r'^addr/$', views.addr, name='addr'),
    url(r'^weixin/$', views.weixin, name='weixin'),
   
    url(r'^hasinform', views.hasinform, name='hasinform'), # lindyang
    url(r'^hastopic/$', views.hastopic, name='hastopic'),

    url(r'^inform/(?P<page>\d+)/$', views.inform, name='inform'),
    url(r'^readinform(?P<pk>[1-9]\d*)/$', views.readinform, name='readinform'),

    url(r'^home/$', views.home, name='home'),
    url(r'^customservice/$', views.customservice, name='customservice'),
    url(r'^credit/$', views.credit, name='credit'),
    
    url(r'^cursor/$', views.cursor, name='cursor'),
    url(r'^project/(?P<cursor>[01234])/(?P<page>\d+)/$', views.project, name='project'),

    url(r'^auth/$', views.auth, name='auth'),

    url(r'^like/(?P<pk>[1-9]\d*)/(?P<flag>[01])/$', views.like, name='like'),
    url(r'^collect/(?P<pk>[1-9]\d*)/(?P<flag>[01])/$', views.collect, name='collect'),
    url(r'^collectfinance/(?P<page>\d+)/$', views.collectfinance, name='collectfinance'),
    url(r'^collectfinancing/(?P<page>\d+)/$', views.collectfinancing, name='collectfinancing'),
    url(r'^collectfinanced/(?P<page>\d+)/$', views.collectfinanced, name='collectfinanced'),



    url(r'^upload/$', views.upload, name='upload'),

    url(r'^newstype/$', views.newstype, name='newstype'),
    url(r'^news/(?P<pk>[1-9]\d*)/(?P<page>\d+)/$', views.news, name='news'),
    url(r'^newsread/(?P<pk>[1-9]\d*)/$', views.newsread, name='newsread'),
    url(r'^newsshare/(?P<pk>[1-9]\d*)/$', views.newsshare, name='newsshare'),
    url(r'^sanban/(?P<name>\d+)/$', views.sanban, name='sanban'),
    url(r'^newssearch/(?P<page>\d+)/$', views.newssearch, name='newssearch'),
    url(r'^sharenews/(?P<pk>[1-9]\d*)/$', views.sharenews, name='sharenews'),

    url(r'^feeling/(?P<page>\d+)/$', views.feeling, name='feeling'),

    url(r'^wantinvest/(?P<pk>[1-9]\d*)/(?P<flag>[01])/$', views.wantinvest, name='wantinvest'),

    url(r'^projectdetail/(?P<pk>[1-9]\d*)/$', views.projectdetail, name='projectdetail'),
    url(r'^financeplan/(?P<pk>[1-9]\d*)/$', views.financeplan, name='financeplan'),
    url(r'^member/(?P<pk>[1-9]\d*)/$', views.member, name='member'),
    url(r'^investlist/(?P<pk>[1-9]\d*)/$', views.investlist, name='investlist'),
    url(r'^attend/(?P<pk>[1-9]\d*)/$', views.attend, name='attend'),

    url(r'^investor/(?P<cursor>[012])/(?P<page>\d+)/$', views.investor, name='investor'),

    url(r'^thinktank/(?P<page>\d+)/$', views.thinktank, name='thinktank'),
    url(r'^thinktankdetail/(?P<pk>[1-9]\d*)/$', views.thinktankdetail, name='thinktankdetail'),

    url(r'^feedback/$', views.feedback, name='feedback'),
    url(r'^keyword/$', views.keyword, name='keyword'),
    url(r'^projectsearch/(?P<page>\d+)/$', views.projectsearch, name='projectsearch'),
    url(r'^userinfo/((?P<pk>[1-9]\d*)/)?$', views.userinfo, name='userinfo'),
    url(r'^myupload/(?P<page>\d+)/$', views.myupload, name='myupload'),
    url(r'^myinvest/(?P<page>\d+)/$', views.myinvest, name='myinvest'),

    url(r'^token/$', views.token, name='token'),
    url(r'^callback/$', views.callback, name='callback'),
    url(r'^delvideo/$', views.delvideo, name='delvideo'),
    url(r'^ismyproject/(?P<pk>[1-9]\d*)/$', views.ismyproject, name='ismyproject'),
    url(r'^valsession/$', views.valsession, name='valsession'),
    url(r'^checkupdate/(?P<system>[12])/$', views.checkupdate, name='checkupdate'),
    url(r'^shareproject/(?P<pk>[1-9]\d*)/$', views.shareproject, name='shareproject'),
    url(r'^shareapp/$', views.shareapp, name='shareapp'),

    url(r'^aboutroadshow', views.aboutroadshow, name='aboutroadshow'),
    url(r'^risk/$', views.risk, name='risk'),
    url(r'^useragreement/$', views.useragreement, name='useragreement'),
    url(r'^projectprotocol/$', views.projectprotocol, name='projectprotocol'),
    url(r'^crowfunding/$', views.crowfunding, name='crowfunding'),
    url(r'^leadfunding/$', views.leadfunding, name='leadfunding'),
    url(r'^privacy/$', views.privacy, name='privacy'),

    url(r'^topic/(?P<pk>[1-9]\d*)/$', views.topic, name='topic'),
    url(r'^topiclist/(?P<pk>[1-9]\d*)/(?P<page>\d+)/$', views.topiclist, name='topiclist'),
    url(r'^mytopiclist/(?P<page>\d+)/$', views.mytopiclist, name='mytopiclist'),
    url(r'^readtopic/(?P<pk>\d+)/$', views.readtopic, name='readtopic'),

    url(r'^latestnewscount/$', views.latestnewscount, name='latestnewscount'),
    url(r'^getfeeling/(?P<pk>[1-9]\d*)/$', views.getfeeling, name='getfeeling'),
    url(r'^postfeeling/$', views.postfeeling, name='postfeeling'),
    url(r'^deletefeeling/(?P<pk>[1-9]\d*)/$', views.deletefeeling, name='deletefeeling'),
    url(r'^likefeeling/(?P<pk>[1-9]\d*)/(?P<is_like>[01])/$', views.likefeeling, name='likefeeling'),
    url(r'^feelinglikers/(?P<pk>[1-9]\d*)/(?P<page>\d+)/$', views.feelinglikers, name='feelinglikers'),
    url(r'^feelingcomment/(?P<pk>[1-9]\d*)/(?P<page>\d+)/$', views.feelingcomment, name='feelingcomment'),
    url(r'^postfeelingcomment/(?P<pk>[1-9]\d*)/$', views.postfeelingcomment, name='postfeelingcomment'),
    url(r'^hidefeelingcomment/(?P<pk>[1-9]\d*)/$', views.hidefeelingcomment, name='hidefeelingcomment'),
    url(r'^background/$', views.background, name='background'),
]
