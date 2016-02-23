# coding: utf-8
from django.shortcuts import render
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login

from phone.models import *
from utils.utils import *
from utils.sanban18 import *

# Create your views here.

import functools
import sys

def annc(req, name):
    return render(req, 'app/annc/%s.html' % name)

def sanban(req, name):
    try:
        return render(req, 'app/sanban/%s' % name)
    except:
        return HttpResponseRedirect('<h1>Page not found</h1>')

def test(request):
    return render(request, 'app/test.html')

def add(request):
    a = request.GET.get('a', '1')
    b = request.GET.get('b', '2')
    c = int(a) + int(b)
    return HttpResponse(c)

def join(request):
    return render(request, 'app/join.html')

def g_project(queryset, page): 
    #from phone.views import project_stage
    #start, end = start_rnd(page, 20)
    start, end = 1, 4
    queryset = queryset[start:end]
    if isinstance(queryset[0], Project): flag = 'p'
    elif isinstance(queryset[0], RecommendProject): flag = 'r'
    elif isinstance(queryset[0], InvestShip): flag = 'i'
    elif isinstance(queryset[0], CollectShip): flag= 'c'
    data = list()
    for i, project in enumerate(queryset):
        tmp = dict()
        if flag == 'r': tmp['reason'] = project.reason
        if flag != 'p': project = project.project
        tmp['id'] = project.id
        company_name = re.sub(r'(股份)?有限(责任)?公司', '', project.company.name)
        tmp['company_name'] = company_name
        tmp['company_profile'] = project.company.profile
        #ret = lcv(project)
        #tmp['like_sum'] = ret['like_sum']
        #tmp['collect_sum'] = ret['collect_sum']
        #tmp['vote_sum'] = ret['vote_sum']
        #stage = project_stage(project)
        #tmp['stage'] = stage
        #if stage['flag'] == 3: tmp['invest_amount_sum'] = project.finance2get # 融资完成的显示
        tmp['invest_amount_sum'] = '399'
        data.append(tmp)
    return data

def index(request):
    data = {'investornum':1000,
        'investamount':8000000,
        'cycle':range(1,21),
    }
    queryset = Project.objects.all()
    ret = g_project( queryset, 0 )
    return render(request, 'app/index.html', {'data': data, 'queryset':ret})

@login_required
def news(request):
    if request.method == 'POST':
        data = request.POST
        html_content = data.get('html_content', '').replace('\r', '')
        DIGEST_RE = re.compile(r'''(?P<title>.+)
(?P<pub_date>.+)
(?P<src>.+)
(?P<img>.+)
(?P<content>.+)
''')
        m = DIGEST_RE.search(html_content)
        if m:
            print(m.groupdict())
        else:
            error_msg = ['', '']
            return render(request, 'app/news.html', {'error_msg': error_msg})

        kw = m.groupdict()
        PARA_RE = re.compile(r'''^
(.+\n)+''', re.M)
        m = PARA_RE.findall(html_content)
        para = ''
        if m:
            for i in m:
                if i.startswith('http'):
                    para += '<img class="img-responsive" src="%s" alt="图片">' % i
                else:
                    para += '<p>' + i + '</p>'
        print(para)
        kw['para'] = para
        print(para)
        for k in kw.keys():
            print(k)
        sanban = SANBAN()
        newstype = NewsType.objects.get(eng='news')
        name = '0' + datetime.now().strftime('%Y%m%d')

        kw['name'] = name
        sanban.html_save(kw)
        try:
            sanban.news_save(newstype, kw)
        except:
            pass
        
        '''import re
        import os
        import codecs
        URL_RE = re.compile( 
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...  
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip 
        r'(?::\d+)?' # optional port 
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        from phone.models import NewsType, News
        from django.db.models import Q
        from datetime import date
        import time
        from jinzht.settings import DOMAIN
        data = request.POST
        newstype = NewsType.objects.filter(~Q(valid=False))[0]
        title = data.get('title', '').strip()
        img = request.FILES.get('img')
        name = '0' + str(int(time.time()))
        pub_date = date.today().strftime('%Y-%m-%d') 
        src = data.get('src', '金指投').strip()
        content = data.get('content', '').strip()
        html_content = data.get('html_content', '').strip()

        print(newstype, title, img, name, pub_date, src, content, html_content)
        error_msg = []
        not title and error_msg.append('标题不能为空')
        not img and error_msg.append('图片不能为空')
        not content and error_msg.append('内容不能为空')
        not html_content and error_msg.append('网页内容不能为空')
        if error_msg:
            return render(request, 'app/news.html', {'error_msg': error_msg})

        dirname = os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) )
        app_label = 'app'
        pth = os.path.join(dirname, app_label, 'templates', app_label, 'sanban') 
        filepath = os.path.join(pth, name)
        with codecs.open(filepath, 'w', 'utf-8') as fp:
            fp.write(html_content)

        pth = os.path.join(dirname, 'media', 'sanban')
        imgpath = os.path.join(pth, name)
        with open(imgpath, 'wb') as fp:
            for chunk in img.chunks():
                fp.write(chunk)
        thumbnail = Thumbnail(imgpath)
        format = thumbnail.resize()
        if not format:
            format = ''
        else:
            format = '.' + format
        
        try:
            news = News.objects.create(
                newstype = newstype,
                title = title,
                img = '%s/media/sanban/%s' % (DOMAIN, name + format),
                name = name,
                pub_date = pub_date,
                src = src,
                content = content,
            )
        except Exception as e:
            os.path.exists(filepath) and os.remove(filepath)
            os.path.exists(imgpath) and os.remove(imgpath)
            error_msg.append(e)
            return render(request, 'app/news.html', {'error_msg': error_msg})
        else:
            return render(request, 'app/news.html', {'success': True}) 
        '''

    return render(request, 'app/news.html', {})

def finance(request):
    return render(request, 'app/finance.html')

def companyfinance(request):
    pk = 1
    item = Project.objects.get(pk=pk)
    #getinstance(Project, pk)
    data = dict()
    data['company'] = item.company.name
    data['img'] = '%s%s' %(RES_URL, item.img.url)

    # 融资计划
    data['planfinance'] = item.planfinance
    data['pattern'] = item.pattern
    data['share2give'] = item.share2give
    data['usage'] = item.usage
    data['quiteway'] = item.quitway

    context = {'data':data}
    return render(request, 'app/companyfinance.html', context)

def investor(request):
    queryset = Investor.objects.all()
    data = list()
    for item in queryset:
        tmp = dict()
        tmp['id'] = item.id
        tmp['photo'] = myimg(item.user.img)
        tmp['name'] = item.user.name
        tmp['create_datetime'] = datetime_filter(item.create_datetime)
        data.append(tmp)
    context = {'data': data}
    return render(request, 'app/investor.html', context)

def thinktank(request):
    queryset = Thinktank.objects.all()
    data = list()
    for item in queryset:
        tmp = dict()
        tmp['id'] = item.id
        tmp['img'] = '%s%s' %(settings.RES_URL, item.img.url)
        tmp['name'] = item.name
        tmp['company'] = item.company
        tmp['title'] = item.title
        tmp['experience'] = item.experience
        tmp['success_cases'] = item.success_cases
        tmp['good_at_field'] = item.good_at_field
        data.append(tmp)
    context = {'data':data}
    return render(request, 'app/thinktank.html', context)

def thinktankdetail(request):
    return render(request, 'app/thinktankdetail.html')

def login(request):
    if request.method == 'GET':
        print(type(request))
        print(dir(request))
        return render(request, 'app/login.html')
    elif request.method == 'POST':
        telephone = request.POST.get('telephone', '').strip()
        if valtel(telephone) == False:
            msg = '手机号码错误'
            return render(request, 'app/login.html', {'msg': msg})
        user = User.objects.filter(telephone=telephone)
        if user.exists():
            password = request.POST.get('password') 
            password = '%s%s%s' % (password, telephone, 'lindyang')
            password = hashlib.md5( password.encode('utf-8') ).hexdigest()
            if password == user[0].password:
                request.session['login'] = user[0].id
                return HttpResponseRedirect( reverse('app:index') ) 
            else:
                return render(request, 'app/login.html', {'msg': '密码错误'})
        return render(request, 'app/login.html', {'msg': '失败'})

def userinfofinance(request):
    return render(request, 'app/userinfofinance.html')

def project(request, pk):
    project = Project.objects.get(pk=pk)
    active = sys._getframe().f_code.co_name
    context = {'project': project}
    return render(request, 'app/project.html', context)

def news_(request, name):
    data = list()
    queryset = []
    for item in queryset:
        tmp = dict()
        tmp['id'] = item.id
        tmp['title'] = item.title
        tmp['source'] = item.source
        tmp['content'] = item.content
        tmp['src'] = item.src
        tmp['sharecount'] = item.sharecount
        tmp['create_datetime'] = datetime_filter(item.create_datetime) 
        tmp['create_datetime'] = timezone.localtime(item.create_datetime).strftime('%m/%d %H:%M')
        tmp['readcount'] = item.readcount
        tmp['href'] = '%s/%s/%s' %(settings.RES_URL, settings.NEWS_URL_PATH, item.name)
        data.append(tmp)
    context = {'data':data}
    return render(request, 'app/news/%s' % name, context)
