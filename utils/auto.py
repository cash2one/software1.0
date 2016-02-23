HTML='''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <title>{title}</title>
    <meta charset="utf-8">
    <meta content="user-scalable=no,width=device-width, initial-scale=1" name="viewport">
    <meta content="Title" name="apple-mobile-web-app-title">
    <meta content="black" name="apple-mobile-web-app-status-bar-style">
    <meta content="True" name="HandheldFriendly">
    <meta content="320" name="MobileOptimized">
    <meta content="pc,mobile" name="applicable-device">
    <link rel="stylesheet" type="text/css" href="http://www.jinzht.com/static/app/css/news.css">
</head>
<style>
</style>
<body>
    <div class="article-detail-wrap reading-off">
        <div class="main-section">
            <div class="content-wrapper">
                <div class="article-section">
                    <div class="inner">
                        <article class="single-post englist-wrap">
                            <section class="single-post-header">
                                <header class="single-post-header__meta">
                                    <h1 class="single-post__title">{title}</h1>
                                </header>
                                <div class="author">
                                    <a href="http://a.app.qq.com/o/simple.jsp?pkgname=com.jinzht.pro">
                                        <span class="name">金指投科技</span>
                                    </a>
                                    <span class="time">&nbsp;•&nbsp;<time class="timeago">{source}</time></span>
                                </div>
                            </section>
                            <section class="article">
                                {para}
                                <div class="two-dimension-code"><img style="margin:0 auto;width:30%;display:block;" src="http://www.jinzht.com/static/app/img/two_dimension_code.png"></div>
                            </section>
                        </article>
                    </div>
                </div>
            </div> <!-- END content-wrapper -->
            <div class="side-box">
                
            </div> <!-- END side-box -->
        </div>
    </div>
</body>
<html>'''
if __name__ == '__main__':
    import os
    import re
    import codecs
    DIGEST_RE = re.compile(r'''(?P<title>.+)
(?P<time>.+)
(?P<src>.+)
(?P<strong>.+)
''')
    PARA_RE = re.compile(r'''^\r
(.+\r\n)+''', re.M)
    cur_dir = os.path.dirname(__file__)
    html_file = os.path.join(cur_dir, 'my.html')
    
    kw = {}
    with codecs.open(html_file, 'r', 'utf-8') as fp:
        #print(fp.readline())
        content = fp.read()
        m = DIGEST_RE.search(content)
        if m:
            kw = m.groupdict()
        m = PARA_RE.findall(content)
        para = ''
        if m:
            for i in m:
                if i.startswith('http'):
                    para += '<div class="firgure"><img src="' + i + '"></div>'
                else:
                    para += '<p>' + i + '</p>'
        kw['para'] = para
        
        html = HTML.format(**kw)
        html_file = os.path.join(cur_dir, 'tmp.html')
        with open(html_file, 'wb') as fp:
            fp.write(bytes(html, 'UTF-8'))
            
        

