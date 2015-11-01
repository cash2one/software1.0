#!/usr/bin/python
# coding=utf8
import random
import socket
from urllib.request import HTTPCookieProcessor, HTTPHandler, install_opener, build_opener
import re
import string
from bs4 import BeautifulSoup
import os
import sys
from http.cookiejar import CookieJar
from datetime import datetime
from jinzht import settings
from phone.models import News


AGENT = [
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
    'Opera/9.25 (Windows NT 5.1; U; en)',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
    'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
    'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
    "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7",
    "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0 ",
]

TOP_RE = re.compile('class="bule">(?P<source>.*?)</span>.*?(?P<pub>\d{4}\-\d{2}\-\d{2})')
DE_RE = re.compile('''<a\ class="htn-a-img"\ href="(?P<href>.*?)".*?>.
    <img\ src="(?P<img>.*?)".*?/>.
    </a>.
    <h3>.
    <a.*?>(?P<title>.*?)</a>.
    </h3>.
    <p>(?P<content>.*?)</p>''', re.VERBOSE | re.DOTALL)

class Browser(object):
    '''模拟浏览器'''
    def __init__(self):
        socket.setdefaulttimeout(20)
        self.HTML = ''

    def open(self, url='http://www.sanban18.com/Industry/'):
        '''打开网页'''
        cookie = HTTPCookieProcessor(CookieJar())
        self.opener = build_opener(cookie, HTTPHandler)
        install_opener(self.opener)
        agent = random.choice(AGENT)
        self.opener.addheaders = [("User-agent", agent), ("Accept", "*/*")]
        try:
            res = self.opener.open(url)
            self.HTML = res.read()
        except Exception as e: print(e)
        else: return res

    def update(self, top, newstype=None):
        m = TOP_RE.search(str(top))
        if not m: return
        source = m.group('source') # source
        pub = m.group('pub') # pub
        de = top.findNextSibling('div', {'class': 'htn-de clearfix'})
        m = DE_RE.search(str(de))
        if not m: return
        img = m.group('img') # 图片
        title = m.group('title').strip() # 标题
        if newstype.eng == 'viewpoint': title = re.sub(r'\[.+?\]', '', title)
        content = m.group('content').strip() # 简短介绍
        url = m.group('href')
        url = url.replace('www.sanban18.com', '61.152.104.238')
        try: self.open(url)
        except Exception as e: print(e)
        soup = BeautifulSoup(self.HTML, 'html.parser')
        div = soup.findAll('div', {'class', 'newscont'})[0]
        div = str(div)
        name = url.rsplit('/', 1)[-1].rsplit('.')[0]
        #year = datetime.now().strftime('%Y')
        #name = '%s/%s' % (year, name) # 网页名
        div = re.sub(r'style=".*?"', '', div)
        div = re.sub(r'href=".*?"', 'href="#"', div)
        div = div.replace(r'<br>"', '')
        div = div.replace('src="/', 'src="http://www.sanban18.com/')
        div = div.replace('src=', 'class="img-responsive" src=')
        print(title)
        try: self.save(name, title, pub, source, div)
        except Exception as e: print(e)
        else:
            try:
                News.objects.create(
                    newstype = newstype,
                    title = title, 
                    img = img, 
                    name = name, 
                    pub_date = pub,
                    source = source,
                    content = content, 
                )
            except Exception as e: print(e) 
            else: print(name, title, pub, source)

    def save(self, name, title, pub, source, div):
        app = 'http://a.app.qq.com/o/simple.jsp?pkgname=com.jinzht.pro'
        html = '''
<!DOCTYPE html>                
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="http://cdn.bootcss.com/bootstrap/3.3.5/css/bootstrap.min.css"/>
        <link href="http://www.jinzht.com/static/app/css/blog.css" rel="stylesheet">
    </head>
    <body>
        <div class="container-fluid">
            <div class="row blog-main" style="margin:5px -14px;">
                <div class="blog-post">
                <h4 style="color:#e94819;"><strong>%s</strong></h4>
                <p class="blog-post-meta">
                    <a href="%s">%s</a>
                    <a class="btn btn-danger pull-right" href="%s">下载APP</a>
                </p>
                %s
                <p class="blog-post-meta">版权: %s</p>
            </div>
        </div>
    </body>
</html>''' % (title, app, '金指投科技', app, div, source)

        import codecs
        pth = os.path.join(settings.BASE_DIR, settings.NEWS_TEMPLATE) 
        filepath = os.path.join(pth, name)
        try: fp = codecs.open(filepath, 'w+', 'utf-8')
        except IOException as e: print(e) 
        fp.write(html) 
        fp.close()

    def collect(self, newstype):
        '''get the main article'''
        soup = BeautifulSoup(self.HTML, 'html.parser')
        tags = soup.findAll('p', {'class': 'htn-top clearfix'})
        for top in tags[0:3]: self.update(top, newstype)

def main():
    browser = Browser()
    try: from phone.models import NewsType
    except Exception as e: exit(0)
    else:
        from django.db.models import Q
        for item in NewsType.objects.filter(~Q(valid=False)):
            print(item.eng, item.name) 
            url = 'http://www.sanban18.com/%s/' %(item.eng)
            url = 'http://61.152.104.238/%s/' %(item.eng)
            try: browser.open(url)
            except Exception as e: print('can not open url')
            else: browser.collect(item)

def push():
    from phone.models import News
    from phone.utils import JG
    from jinzht import settings
    news = News.objects.all()
    if not news: return
    else: news = news[0]
    if news.newstype.id == 4: api="news"
    else: api="knowledge"
    url = "%s/%s/%s" %(settings.RES_URL, settings.NEWS_URL_PATH, news.name)
    extras = {"api": api, '_id':news.id, "url": url}
    #JiGuang(news.title, extras).all()
    JG(news.title, extras).single('050eb8bcd2f')
    JG(news.title, extras).single('050dee23230')
    JG(news.title, extras).single('040013e6333')
    
if __name__ == '__main__':
    main()
