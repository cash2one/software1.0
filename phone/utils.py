#!/usr/bin/python
# coding: utf-8
__author__ = 'lindyang'
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders

from django.core.files import File
from django.utils import timezone
import pytz
from datetime import datetime, timedelta, date
from rest_framework.response import Response

import os, re, functools, uuid, time, random, pytz, hashlib
import jpush as jpush
import requests
from qiniu import Auth, BucketManager
try:
    from jinzht import settings
except ImportError:
    print('ImportError')
else:
    ISEXISTS = Response({'status':1, 'msg':'不存在实体'})                 
    ARG = Response({'status':1, 'msg':'参数错误'})

RES_URL = settings.RES_URL 
PHONE_RE = re.compile(r'(13[0-9]|15[012356789]|17[678]|18[0-9]|14[57])[0-9]{8}$')
PAGE_SIZE = 4        
PK_RE = re.compile(r'^[1-9]\d*$')
MTM_RE = re.compile(r'^[1-9]\d*(,[1-9]\d*)*$')

def mystorage_file(file_field, upload_file, upload_to=''):
    name = upload_file.name
    pth = datetime.now().strftime(upload_to)
    file_field.save('%s/%s' % (pth, name), File(upload_file)) 
        
def myarg(field='参数'):
    return Response({'status':1, 'msg':'%s 错误' % field})

def myimg(file, default=''):
    if not file:
        return '%s/media/default/coremember.png' % settings.RES_URL
    else:
        return '%s%s' % (settings.RES_URL, file.url)

def timeformat(now=timezone.now()):
    return timezone.localtime(now).strftime('%Y-%m-%d %H:%M:%S')

def dateformat(now=timezone.now()):
    return timezone.localtime(now).strftime('%Y-%m-%d')

def validate_telephone(telephone):
    if telephone and PHONE_RE.match(telephone): return True
    return False                              

def datetime_filter(t):
    t = time.mktime(timezone.localtime(t).timetuple())
    delta = int(time.time() - t)
    if delta < 60:
        return '1分钟前'
    if delta < 3600:
        return '%s分钟前' % (delta//60)
    if delta < 86400:
        return '%s小时前' % (delta//3600)
    if delta < 604800:
        return '%s天前' % (delta//86400)
    dt = datetime.fromtimestamp(t)
    return '%s年%s月%s日' % (dt.year, dt.month, dt.day)

def start_end(page=0, page_size=PAGE_SIZE):        
    page = int(page)
    page_size = int(page_size)
    start = page * page_size
    end = (page+1) * page_size
    return start, end

def islogin(text=''):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            uid = args[0].session.get('login')
            if not uid or not PK_RE.match('%s' %uid):
                return Response({'status':-99, 'msg':'请登录'})
            return func(*args, **kw)
        return wrapper
    return decorator

class MobSMS:
    userid = settings.userid 
    account = settings.account
    password = settings.password 
    remainpoint = re.compile(r'<remainpoint>(\d{1,})</remainpoint>')
    overage = re.compile(r'<overage>(\d{1,})</overage>')
    def __init__(self, code='123456'):
        self.code = code
        self.msg = "验证码%s. 金指投科技, 十分钟内有效" % (code)
        self.url = settings.msg_url % 'send' 

    def send(self, mobile, sendTime=''):
        data = {
            'userid': MobSMS.userid, 
            'account': MobSMS.account,
            'password': MobSMS.password, 
            'mobile': mobile, 
            'content': self.msg, 
            'sendtime': sendTime
        }
        req = requests.post(self.url, data=data, verify=False)
        ret = req.content.decode('utf-8')
        m = MobSMS.remainpoint.search(ret)
        if m: return m.group(1)
        else: return -1
    
    def remind(self, mobile, msg='test', sendTime=''):
        data = {
            'userid': MobSMS.userid, 
            'account': MobSMS.account,
            'password': MobSMS.password, 
            'mobile': mobile, 
            'content': msg, 
            'sendtime': sendTime
        }
        req = requests.post(self.url, data=data, verify=False)
        ret = req.content.decode('utf-8')
        m = MobSMS.remainpoint.search(ret)
        if m: return m.group(1)
        else: return -1
    
    def check(self):
        data = {
            'userid': MobSMS.userid, 
            'account': MobSMS.account,
            'password': MobSMS.password, 
        }
        url = settings.msg_url % 'overage'
        req = requests.post(url, data=data, verify=False)
        ret = req.content.decode('utf-8')
        m = MobSMS.overage.search(ret)
        if m: return m.group(1)
        else: return -1

class MAIL(object):
    server =  settings.mail_server
    fro = settings.mail_server['user'] 
    
    def __init__(self, subject, text, files=[], to=settings.mail_to):
        self.subject = subject
        self.text = text
        self.files = files
        self.to = to

    def send(self):
        assert type(MAIL.server) == dict
        assert type(self.to) == tuple 
        assert type(self.files) == list
        msg = MIMEMultipart()
        msg['From'] = MAIL.fro
        msg['Subject'] = self.subject
        msg['To'] = COMMASPACE.join(self.to)
        msg['Date'] = formatdate(localtime=True)
        msg.attach(MIMEText(self.text))

        for file in self.files:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(open(file, 'rb').read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 
                'attachment; filename="%s"' % os.path.basename(file))
            msg.attach(part)
        
        import smtplib
        smtp = smtplib.SMTP(MAIL.server['name'])
        smtp.login(MAIL.server['user'], MAIL.server['passwd'])
        smtp.sendmail(MAIL.fro, self.to, msg.as_string())
        smtp.close()

class JiGuang(object):
    app_key = settings.app_key 
    master_secret = settings.master_secret

    def __init__(self, msg='金指投', extras={}):
        self.msg = msg
        self.ios_msg = jpush.ios(
            alert=msg , 
            badge="+1", 
            sound="a.caf", 
            extras=extras
        )
        self.android_msg = jpush.android(
            alert=msg,
            extras=extras
        )
        self.push = jpush.JPush(
            JiGuang.app_key, 
            JiGuang.master_secret
        ).create_push() 

    def all(self):
        self.push.audience = jpush.all_
        self.push.notification = jpush.notification(
            alert=self.msg, 
            android=self.android_msg, 
            ios=self.ios_msg
        ) 
        self.push.options = {
            "time_to_live":86400, 
            "sendno":12345,
            "apns_production":False
        }
        self.push.platform = jpush.all_  
        self.push.send()

    def single(self, reg_id):
        self.push.audience = jpush.audience( 
            jpush.registration_id('id1', reg_id) 
        ) 
        self.push.notification = jpush.notification(
            alert=self.msg, 
            android=self.android_msg, 
            ios=self.ios_msg
        ) 
        self.push.options = {
            "time_to_live":86400, 
            "sendno":12345,
            "apns_production":False
        }
        self.push.platform = jpush.all_ 
        self.push.send() 

if __name__ == '__main__':
    print('yld') 
