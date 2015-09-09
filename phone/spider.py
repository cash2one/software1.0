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
from .models import News

ERROR = {
    '0': 'cant not open the url, check your net',
    '1': 'create download dir error',
    '2': 'the image links is empty',
    '3': 'download failed',
    '4': 'build soup error, the html is empty',
    '5': 'can not save the image to your disk',
}

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

NEWS_RE = re.compile(r'''
<div\ class="Q-tpWrap">
    <a\ .+?href="(?P<href>.+?)".+?>
        <img\ src="(?P<src>.+?)"/>
    </a>
    <a\ .+?>(?P<title>.+?)</a>
    <p\ class="intro">
        <a\ .+?>(?P<content>.+?)</a>
        <br>
        <b>(?P<date>.+?)</b>
        </br>
    </p>
</div>''', re.VERBOSE)

SK_RE = re.compile(r'来源:(?P<source>.+?)\xa0+?关键词:(?P<keyword>.+?)\r')

class Browser(object):
    '''模拟浏览器'''
    def __init__(self):
        socket.setdefaulttimeout(20)
        self.HTML = ''

    def open(self, url='http://www.xsbcc.com/news/newslist1.html'):
        '''打开网页'''
        cookie = HTTPCookieProcessor(CookieJar())
        self.opener = build_opener(cookie, HTTPHandler)
        install_opener(self.opener)
        agent = random.choice(AGENT)
        self.opener.addheaders = [("User-agent", agent), ("Accept", "*/*")]
        try:
            res = self.opener.open(url)
            self.HTML = res.read()
        except Exception as e:
            raise Exception
        else:
            return res

    def update(self, tags):
        values = NEWS_RE.finditer(str(tags))
        for value in values:
            href = value.group('href') 
            url = 'http://www.xsbcc.com%s' % href 

            title = value.group('title').strip() # 标题
            src = value.group('src') # 图片
            content = value.group('content') # 简短介绍
            pub = value.group('date').strip() # 发布时间 
            self.open(url)
            soup = BeautifulSoup(self.HTML, 'html.parser')
            head = soup.findAll('div', {'class', 'info'})[0]
            detail = soup.findAll('div', {'class', 'rcon'})[0]
            sk = SK_RE.search(str(head))

            source = sk.group('source').strip() # 来源
            keyword = sk.group('keyword').strip() # 关键词

            name = href.rsplit('/', 1)[-1].rsplit('.')[0]
            #year = datetime.now().strftime('%Y')
            #name = '%s/%s' % (year, name) # 网页名
            DP_RE = re.compile(r'<div><span.*?>(.+?)</span></div>', re.DOTALL)
            div = ''
            for val in DP_RE.finditer(str(detail)):
                div += '<p>%s</p>' % val.group(1)
            try:
                self.save(name, title, pub, source, div)
            except Exception as e:
                print(e)
            else:
                continue
                News.objects.create(
                    title = title, src = src, name = name, source = source,
                    content = content, keyword = keyword
                )
                print(name, 'successfully')

    def save(self, name, title, pub, source, div):
        html = '''
<!DOCTYPE html>                
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="http://cdn.bootcss.com/bootstrap/3.3.5/css/bootstrap.min.css"/>
        <link rel="stylesheet" href="http://getbootstrap.com/2.3.2/assets/css/bootstrap-responsive.css"/>
        <link href="http://www.jinzht.com/static/app/css/blog.css" rel="stylesheet">
    </head>
    <body>
        <div class="container-fluid" style="margin-top:15px;">
            <div class="row"><div class="col-sm-8 blog-main" style="padding-left:0px;padding-right:0px"><div class="blog-post">
            <h3>%s</h3>
            <p class="blog-post-meta">%s by <a href="#">%s</a></p>
            %s
        </div></div></div>
    </body>
</html>''' % (title, pub, source, div)

        import codecs
        pth = '/var/www/html/software1.0/app/templates/app/news/'
        filepath = os.path.join(pth, name)
        try: fp = codecs.open(filepath, 'w+', 'utf-8')
        except: raise 
        fp.write(html) 
        fp.close()

    def collect(self):
        '''get the main article'''
        soup = BeautifulSoup(self.HTML, 'html.parser')
        tags = soup.findAll('div', {'class': 'Q-tpWrap'})
        self.update(tags)

if __name__ == '__main__':
    
    browser = Browser()
    url = 'http://www.xsbcc.com/news/newslist1.html'
    browser.open(url)
    browser.collect()
