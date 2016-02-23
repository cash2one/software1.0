#!/usr/bin/python
# coding=utf8
from urllib.request import HTTPCookieProcessor, HTTPHandler, install_opener, build_opener
from bs4 import BeautifulSoup
import os, sys, string, re, random, socket, codecs
from http.cookiejar import CookieJar
from datetime import datetime
from jinzht import settings
from phone.models import News
from urllib.request import pathname2url

HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="http://cdn.bootcss.com/bootstrap/3.3.5/css/bootstrap.min.css">
</head>
<style>
{style}
</style>
<body>
<div class="container-fluid">
    <div class="row">
        <div class="col-xs-12 col-sm-12 col-md-offset-2 col-md-8 col-lg-offset-2 col-lg-8 article">
            <div>
                <header>
                    <h2>{title}</h2>
                    <div>
                        <em>{pub_date}</em>
                        <em>{src}</em>
                        <em class="download"><span class="glyphicon glyphicon-download-alt" aria-hidden="true"></span>
                            <a href="http://a.app.qq.com/o/simple.jsp?pkgname=com.jinzht.pro">下载金指投</a>
                        </em>
                    </div>
                </header>
                
            </div>
            <div class="para">
                <fieldset class="fieldset">
                    <legend class="legend">金指投</legend>
                    <ul>
                        <li>专注成长型企业股权投融资</li>
                        <li>搭建中小企业融资与上市平台</li>
                        <li>为优秀项目提供私募股权和风险投资</li>
                    </ul>
                </fieldset>
            </div>
            <div class="para">
                {para}
            </div>
            <footer>
                <div class="two-dimension-code row">
                    <div class="col-xs-4 col-sm-4 col-md-offset-1 col-md-4 col-lg-offset-1 col-lg-4">
                    <img src="http://www.jinzht.com/static/app/img/two_dimension_code.png" class="img-responsive" alt="二维码">
                    </div>
                    <div class="col-xs-8 col-sm-8 col-md-7 col-lg-7 desc">
                    <h4><a href="http://v.qq.com/page/s/h/w/s01699sj5hw.html">金指投科技</a></h4>
                    <h5>中国成长型企业股权投融资</h5>
                    </div>
                </div>
            </footer>
        </div>
    </div>
</div>
</body>
</html>'''

STYLE = '''
body {
    background-color: #e9eaec;
    font-family: "Lantinghei SC", "Open Sans", Arial, "Hiragino Sans GB", "Microsoft YaHei", "微软雅黑", "STHeiti", "WenQuanYi Micro Hei", SimSun, sans-serif;
}
.article {
    background-color: #fff;
}
div.para {
    font-size: 17px;
    line-height: 1.8;
    word-wrap: break-word;
    margin-top:30px;
    margin-bottom: 30px;
}
div.para > p {
    text-indent: 2em;
    text-align: justify;
    margin-bottom: 30px;
}
header > h2 {
    padding-bottom: 14px;
    border-bottom: 1px solid #e7e7eb;
}
header > div {
    font-size: 16px;
    vertical-align: middle;
}
header > div > em {
    font-style: normal;
    color: #8c8c8c;
    margin-right: 10px;
}
header > div > em.download {
    float: right;
    positon: relative;
}
header > div > em.download a {
    color: white;
    font-weight: bold;
    text-shadow: 1px 1px 5px #FF0000;
}
legend.legend, fieldset.fieldset ul li {
    font-size: 15px;
    color: #E29716;
}
fieldset.fieldset{
    border: 2px solid #e7e7eb;
    margin:0 auto;
    border-radius: 4px;
    box-shadow: 5px 5px 5px #888888;
}
legend.legend {
    margin: 0 auto;
    border-bottom-width: 0;
    display: inline-block;
    width:inherit;
    padding: 10px;
}
ul {
    list-style-type: circle;
    list-style-position: inside;
    border: 0px solid red;
    margin: 0 auto;
    width: 80%;
    margin-bottom: 20px;
    padding-left:0;
}
.two-dimension-code {
    border-radius: 4px;
    box-shadow: 5px 5px 5px #888888;
    border: 2px solid #e7e7eb;
    z-index: 100%;
    margin: 1px;
    vertical-align: middle;
    padding-top:20px;
    padding-bottom: 20px;
    background: #e9eaec;
}
div.desc {
    text-align:center;
}
div.desc > h5 {
    padding-top: 10px;
    border-top: 2px solid #e7e7eb;
}
div.para img {
    width: 100%;
    margin-bottom: 30px;
}
footer {
    margin-bottom: 30px;
}
'''

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

TOP_RE = re.compile('class="bule">(?P<src>.*?)</span>.*?(?P<pub_date>\d{4}\-\d{2}\-\d{2})')
DE_RE = re.compile('''<a\ class="htn-a-img"\ href="(?P<url>.*?)".*?>.
    <img\ src="(?P<img>.*?)".*?/>.
    </a>.
    <h3>.
    <a.*?>(?P<title>.*?)</a>.
    </h3>.
    <p>(?P<content>.*?)</p>''', re.VERBOSE | re.DOTALL)


class Credit(object):

    LINK_RE = re.compile(r'href="(?P<url>.*?)" target="_blank">(?P<title>.*?)</a></h3>.*?<div class="c-abstract( c-abstract-en)?">(<span class=".+?">(?P<date>.+?)</span>)?(?P<content>.*?)</div>.*<(a|span) class="c-showurl".*?>(?P<origin_url>.+?)</(a|span)>')

    def __init__(self):
        socket.setdefaulttimeout(20)
        cookie = HTTPCookieProcessor(CookieJar())
        opener = build_opener(cookie, HTTPHandler)
        install_opener(opener)
        agent = random.choice(AGENT)
        opener.addheaders = [("User-agent", agent), ("Accept", "*/*")]
        self.opener = opener

    def outcome(self, wd):
        wb = pathname2url(wd)
        url = 'http://www.baidu.com/s?wd=' + wb
        html = self.opener.open(url).read()
        soup = BeautifulSoup(html, 'html.parser')
        divs = soup.findAll('div', {'class':'result c-container '})
        data = []
        for div in divs: 
            m = Credit.LINK_RE.search(str(div))
            m and data.append(m.groupdict())
        return data

class SANBAN(object):

    def __init__(self):

        socket.setdefaulttimeout(20)
        cookie = HTTPCookieProcessor(CookieJar())
        opener = build_opener(cookie, HTTPHandler)
        install_opener(opener)
        agent = random.choice(AGENT)
        opener.addheaders = [("User-agent", agent), ("Accept", "*/*")]
        self.opener = opener

    def update(self, top, newstype=None):
        m = TOP_RE.search(str(top))
        if not m: 
            return
        src = m.group('src') # src
        pub_date = m.group('pub_date') # pub_date
        de = top.findNextSibling('div', {'class': 'htn-de clearfix'})
        m = DE_RE.search(str(de))
        if not m: 
            return
        img = m.group('img') # 图片
        title = m.group('title').strip() # 标题
        if newstype.eng == 'viewpoint': 
            title = re.sub(r'\[.+?\]', '', title)
        content = m.group('content').strip() # 简短介绍
        url = m.group('url')
        html = self.opener.open(url).read()
        soup = BeautifulSoup(html, 'html.parser')
        div = str(soup.findAll('div', {'class', 'newscont'})[0])
        name = url.rsplit('/', 1)[-1].rsplit('.')[0]
        div = re.sub(r' style=".*?"', '', div)
        DAOLUN_RE = re.compile(r'<p>\n<strong>.+?【导语】.+?</p>', re.DOTALL)
        div = DAOLUN_RE.sub('', div, 1) 
        div = re.sub(r'<a .+?>(<strong>)?(.+?)(?(1)</strong>)</a>', r'\2', div)
        div = div.replace(r'<br>', '')
        div = div.replace('src="/', 'src="http://www.sanban18.com/')
        print(title)
        try: 
            kw = {
                'title': title,
                'img': img,
                'name': name,
                'pud_date': pub_date,
                'content': content,
                'src': src,
                'para': div,
            }
            self.html_save(kw)
        except Exception as e: print(e)
        else:
            try: self.news_save(kw)
            except Exception as e: print(e) 
            else: print(name, title, pub_date, src)

    def news_save(self, newstype, kw):
            News.objects.create(
                newstype = newstype,
                title = kw['title'], 
                img = kw['img'], 
                name = kw['name'], 
                pub_date = kw['pub_date'],
                src = kw['src'],
                content = kw['content'], 
            )
        
    def html_save(self, kw):
        kw['style'] = STYLE
        html = HTML.format(**kw)
        dirname = os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) )
        app_label = 'app'
        pth = os.path.join(dirname, app_label, 'templates', app_label, 'sanban') 
        filepath = os.path.join(pth, kw['name'])
        try: fp = codecs.open(filepath, 'w+', 'utf-8')
        except: return
        fp.write(html) 
        fp.close()

    def collect(self, newstype, url):
        html = self.opener.open(url).read()
        soup = BeautifulSoup(html, 'html.parser')
        tags = soup.findAll('p', {'class': 'htn-top clearfix'})
        for top in tags[0:3]: 
            self.update(top, newstype)

def main():
    sanban = SANBAN()
    try:
        from phone4.models import NewsType
    except ImportError:
        from phone.models import NewsType
    from django.db.models import Q
    for item in NewsType.objects.filter(~Q(valid=False)):
        print(item.eng, item.name) 
        url = 'http://61.152.104.238/%s/' %(item.eng)
        try: 
            sanban.collect(item, url)
        except: 
            print('can not open url')

def push():
    from phone.models import News
    from phone.utils import JG
    from jinzht import settings
    news = News.objects.all()
    if not news: return
    else: news = news[0]
    url = "%s/%s/%s" %(settings.DOMAIN, 'phone4/sanban', news.name)
    extras = {"api": 'web', 'id':news.id, "url": url}
    #JiGuang(news.title, extras).all()
    JG(news.title, extras).single('050eb8bcd2f')
    JG(news.title, extras).single('050dee23230')
    JG(news.title, extras).single('040013e6333')
    
if __name__ == '__main__':
    main()
