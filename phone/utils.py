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

import os, re, uuid, time, random, pytz, hashlib, codecs
import imghdr
import jpush as jpush
import requests
from qiniu import Auth, BucketManager
from jinzht import settings


def mystorage_file(file_field, upload_file, upload_to=''):
    name = upload_file.name
    pth = datetime.now().strftime(upload_to)
    file_field.save('%s/%s' % (pth, name), File(upload_file)) 

def myarg(field='参数'):
    return Response({'status':1, 'msg':'%s 错误' % field})

def myimg(file, default=''):
    if not file: return '%s/media/default/coremember.png' % settings.RES_URL
    return '%s%s' % (settings.RES_URL, file.url)

def timeformat(now=timezone.now()):
    if not now: return '待定'
    return timezone.localtime(now).strftime('%Y-%m-%d %H:%M:%S')

def dateformat(now=timezone.now()):
    if not now: return '待定' 
    return timezone.localtime(now).strftime('%Y-%m-%d')

def validtel(tel):
    PHONE_RE = re.compile(r'(13[0-9]|15[012356789]|17[678]|18[0-9]|14[57])[0-9]{8}$')
    if tel and PHONE_RE.match(tel): return True
    return False                              

def dt_(t):
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




def mkdirp(path):
    import errno
    try: os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path): pass
        else: raise

class SMS(object):

    def __init__(self, tel, msg=''):
        
        self.code = ''
        if not msg: 
            self.code = random.randint(1000, 9999)
            msg = "验证码 %s , 十分钟内有效" % self.code
        self.data = { 'userid': settings.SMS_USERID,
            'account': settings.SMS_ACCOUNT,
            'password': settings.SMS_PASSWORD, 
            'mobile': tel, 
            'content': msg}

    def send(self):
        req = requests.post(settings.SMS_URL, data=self.data, verify=False)
        ret = req.content.decode('utf-8')
        remainpoint = re.compile(r'<remainpoint>(\d{1,})</remainpoint>')
        m = remainpoint.search(ret)
        if m: return self.code 
        else: return False
    

class MAIL(object):
    
    def __init__(self, subject, text, files=[], to=settings.MAIL_TO):
        self.subject = subject
        self.text = text
        self.files = files
        self.to = to

    def send(self):
        assert type(self.to) == tuple 
        assert type(self.files) == list
        msg = MIMEMultipart()
        msg['From'] = settings.MAIL_SERVER_USER
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
        smtp = smtplib.SMTP(settings.MAIL_SERVER_NAME)
        smtp.login(settings.MAIL_SERVER_USER, settings.MAIL_SERVER_PASSWD)
        smtp.sendmail(settings.MAIL_SERVER_USER, self.to, msg.as_string())
        smtp.close()

class JG(object):
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
            JG.app_key, 
            JG.master_secret
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
