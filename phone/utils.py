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

COMPANY_RE  = re.compile(r'(股份)?有限(责任)?公司')
def timeformat(now=timezone.now()):
    if not now: return '待定'
    return timezone.localtime(now).strftime('%Y-%m-%d %H:%M:%S')

def dateformat(now=timezone.now()):
    if not now: return '待定' 
    return timezone.localtime(now).strftime('%Y-%m-%d')

def valtel(tel):
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


def checkIdcard(idcard):

    Errors=[
        '验证通过!',
        '身份证号码位数不对!',
        '身份证号码出生日期超出范围或含有非法字符!',
        '身份证号码校验错误!',
        '身份证地区非法!'
    ]

    area={"11":"北京","12":"天津","13":"河北","14":"山西","15":"内蒙古","21":"辽宁","22":"吉林","23":"黑龙江","31":"上海","32":"江苏","33":"浙江","34":"安徽","35":"福建","36":"江西","37":"山东","41":"河南","42":"湖北","43":"湖南","44":"广东","45":"广西","46":"海南","50":"重庆","51":"四川","52":"贵州","53":"云南","54":"西藏","61":"陕西","62":"甘肃","63":"青海","64":"宁夏","65":"新疆","71":"台湾","81":"香港","82":"澳门","91":"国外"}

    idcard=str(idcard)
    idcard=idcard.strip()
    idcard_list=list(idcard)
    #地区校验
    if(not area[(idcard)[0:2]]):
        return False, Errors[4]
    #15位身份号码检测
    if(len(idcard)==15):
        if((int(idcard[6:8])+1900) % 4 == 0 or((int(idcard[6:8])+1900) % 100 == 0 and (int(idcard[6:8])+1900) % 4 == 0 )):
            erg=re.compile('[1-9][0-9]{5}[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))[0-9]{3}$')#//测试出生日期的合法性
        else:
            ereg=re.compile('[1-9][0-9]{5}[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))[0-9]{3}$')#//测试出生日期的合法性
        if(re.match(ereg,idcard)):
            return True, Errors[0]
        else:
            return False, Errors[2]
    #18位身份号码检测
    elif(len(idcard)==18):
        #出生日期的合法性检查
        #闰年月日:((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))
        #平年月日:((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))
        if(int(idcard[6:10]) % 4 == 0 or (int(idcard[6:10]) % 100 == 0 and int(idcard[6:10])%4 == 0 )):
            ereg=re.compile('[1-9][0-9]{5}19[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))[0-9]{3}[0-9Xx]$')#//闰年出生日期的合法性正则表达式
        else:
            ereg=re.compile('[1-9][0-9]{5}19[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))[0-9]{3}[0-9Xx]$')#//平年出生日期的合法性正则表达式
        #//测试出生日期的合法性
        if(re.match(ereg,idcard)):
            #//计算校验位
            S = (int(idcard_list[0]) + int(idcard_list[10])) * 7 + (int(idcard_list[1]) + int(idcard_list[11])) * 9 + (int(idcard_list[2]) + int(idcard_list[12])) * 10 + (int(idcard_list[3]) + int(idcard_list[13])) * 5 + (int(idcard_list[4]) + int(idcard_list[14])) * 8 + (int(idcard_list[5]) + int(idcard_list[15])) * 4 + (int(idcard_list[6]) + int(idcard_list[16])) * 2 + int(idcard_list[7]) * 1 + int(idcard_list[8]) * 6 + int(idcard_list[9]) * 3
            Y = S % 11
            M = "F"
            JYM = "10X98765432"
            M = JYM[Y]#判断校验位
            if(M == idcard_list[17]):#检测ID的校验位
                return True, Errors[0]
            else:
                return False, Errors[3]
        else:
            return False, Errors[2]
    else:
        return False, Errors[1]


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

    def __init__(self, msg='金指投', extras={}):

        self.msg = msg
        self.ios_msg = jpush.ios(
            alert=msg , 
            badge="+1", 
            sound="a.caf", 
            extras=extras
        )
        self.android_msg = jpush.android( alert=msg, extras=extras)
        self.push = jpush.JPush(settings.JAK, settings.JMS).create_push() 


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
        try:
            self.push.send() 
        except Exception as e:
            print(e)

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
        try:
            self.push.send() 
        except Exception as e:
            print(e)

if __name__ == '__main__':
    print('yld') 
