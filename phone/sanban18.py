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
    #LINK_RE = re.compile(r'href="(?P<url>.*?)" target="_blank">(?P<title>.*?)</a></h3>.*?<div class="c-abstract( c-abstract-en)?">(<span class=".+?">(?P<date>.+?)</span>)?(?P<content>.*?)</div>')

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
        url = url.replace('www.sanban18.com', '61.152.104.238')
        html = self.opener.open(url).read()
        soup = BeautifulSoup(html, 'html.parser')
        div = str(soup.findAll('div', {'class', 'newscont'})[0])
        name = url.rsplit('/', 1)[-1].rsplit('.')[0]
        div = re.sub(r' style=".*?"', '', div)
        DAOLUN_RE = re.compile(r'<p>\n<strong>.+?【导语】.+?</p>', re.DOTALL)
        div = DAOLUN_RE.sub('', div, 1) 
        div = re.sub(r'<a .+?>(<strong>)?(.+?)(?(1)</strong>)</a>', r'\2', div)
        #div = div.replace(r'<br>"', '')
        div = div.replace('src="/', 'src="http://www.sanban18.com/')
        print(title)
        try: 
            kw = {
                'name': name,
                'title': title,
                'content': content,
                'date': pub_date,
                'src': src,
                'div': div,
                'two_dimension_code': 'http://www.jinzht.com/static/app/img/two_dimension_code.png',
            }
            self.save(kw)
        except Exception as e:
            print(e)
        else:
            try:
                News.objects.create(
                    newstype = newstype,
                    title = title, 
                    img = img, 
                    name = name, 
                    pub_date = pub_date,
                    src = src,
                    content = content, 
                )
            except Exception as e:
                print(e) 
            else: 
                print(name, title, pub_date, src)

    def save(self, kw):
        HTML = '''
<!DOCTYPE html>
<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=0">
<link rel="shortcut icon" type="image/x-icon" href="http://res.wx.qq.com/mmbizwap/zh_CN/htmledition/images/icon/common/favicon22c41b.ico">
<title>{title}</title>
<link rel="stylesheet" type="text/css" href="http://res.wx.qq.com/mmbizwap/zh_CN/htmledition/style/page/appmsg/page_mp_article_improve2a26bd.css">
<link href="http://res.wx.qq.com/mmbizwap/zh_CN/htmledition/style/page/appmsg/not_in_mm2637ae.css" type="text/css" rel="stylesheet"></head>
<body id="activity-detail" class="zh_CN mm_appmsg not_in_mm" ontouchstart="">
<div id="js_cmt_mine" class="discuss_container editing access" style="display:none;">
    <div class="discuss_container_inner">
        <h2 class="rich_media_title">{title}</h2>
    </div>
</div>

<div id="js_article" class="rich_media">
    <div class="rich_media_inner">
        <div id="page-content">
            <div id="img-content" class="rich_media_area_primary">
                <h2 class="rich_media_title" id="activity-name">
                    {title} 
                </h2>
                <div class="rich_media_meta_list">
                    <em id="post-date" class="rich_media_meta rich_media_meta_text">{date}</em>
                    <em class="rich_media_meta rich_media_meta_text">金指投</em>
                    <a class="rich_media_meta rich_media_meta_link rich_media_meta_nickname" href="javascript:void(0);" id="post-user">{src}</a>
                    <span class="rich_media_meta rich_media_meta_text rich_media_meta_nickname">{src}</span>
                </div>
                <div class="rich_media_content " id="js_content">
                    <p><em>{content}</em></p>
                    <p><br></p>
                    {div}
                    <img src="{two_dimension_code}" style="width: auto ! important; visibility: visible ! important; height: auto ! important;" data-s="300,640" data-type="jpeg" data-ratio="1" data-w="">
                </div>
                <link rel="stylesheet" type="text/css" href="http://res.wx.qq.com/mmbizwap/zh_CN/htmledition/style/page/appmsg/page_mp_article_improve_combo29ab01.css">
                <div id='js_toobar3" class="rich_media_tool">
                    <a class="media_tool_meta meta_primary" id="js_view_source" href="http://a.app.qq.com/o/simple.jsp?pkgname=com.jinzht.pro">下载APP, 阅读原文</a>
                </div>
            </div>
        </div>
        <div id="js_pc_qr_code" class="qr_code_pc_outer" style="display: block;">
            <div class="qr_code_pc_inner">
                <div class="qr_code_pc">
                    <img src="{two_dimension_code}" id="js_pc_qr_code_img" class="qr_code_pc_img">
                    <p>微信扫一扫<br>下载该APP</p>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>'''.format(**kw)
        dirname = os.path.dirname( os.path.abspath(__file__) )
        app_label = os.path.basename(dirname)
        pth = os.path.join(dirname, 'templates', app_label, 'sanban') 
        filepath = os.path.join(pth, kw['name'])
        try: 
            fp = codecs.open(filepath, 'w+', 'utf-8')
        except:
            return
        fp.write(HTML) 
        fp.close()

    def collect(self, newstype, url):
        html = self.opener.open(url).read()
        soup = BeautifulSoup(html, 'html.parser')
        tags = soup.findAll('p', {'class': 'htn-top clearfix'})
        for top in tags[0:3]: 
            self.update(top, newstype)

def main():
    sanban = SANBAN()
    from phone4.models import NewsType
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
