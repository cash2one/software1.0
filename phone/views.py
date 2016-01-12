# coding: utf-8
__author__ = 'lindyang'

from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Coalesce
from collections import OrderedDict
from phone.models import *
from phone.utils import *
import functools
from jinzht.config import QUALIFICATION, INDUSTRY
from PIL import Image as Img
from io import StringIO

from django.http import Http404
from django.http import HttpResponseNotFound

PK_RE = re.compile(r'^[1-9]\d*$')
MTM_RE = re.compile(r'^[1-9]\d*(,[1-9]\d*)*$')
CHINESE_RE = re.compile(r'[\u4e00-\u9fa5a-zA-Z]+')

ENTITY = Response({'code': -2, 'msg': '非法操作'})

def r(code, msg=''):
    return Response({'code': code, 'msg': msg}) 

def r_(code, data, msg=''):
    return Response({'code': code, 'msg': msg, 'data': data})

def q(QuerySet, page, size=4):
    if not QuerySet: 
        return []
    page, size = int(page), int(size)
    s = page * size
    e = (page+1) * size
    return QuerySet[s:e]

def i(Model, pk):
    if not pk: return None
    model = Model.objects.filter(pk=pk)
    return model[0] if model.exists() else None

def s(req):
    return req.session.get('uid')

def u(req):
    return User.objects.get(pk=req.session.get('uid'))

def login(text=''):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            uid = args[0].session.get('uid')
            if not uid or not PK_RE.match('%s' %uid):
                return Response({'code': -1, 'msg': func.__name__})
            return func(*args, **kw)
        return wrapper
    return decorator


def store(field, image):
    if not image: 
        return False
    ext = imghdr.what(image)
    if ext not in ('jpeg', 'png'):
        return False
    print(image.size)
    if False and image.size > 100000:
        img = Img.open(image.read())
        #img.thumbnail((image.width/1.5, image.height/1.5), Img.ANTIALIAS)
        output = StringIO()
        img.save(output, format='JPEG', quality=20)
        output.seek(0)
        print(output.len)
        image= InMemoryUploadedFile(output,'ImageField', "file.jpg", 'image/jpeg', output.len, None)
    
    field.save('file.jpg', File(image)) 
    return True


def img(file, default=''):
    if not file: 
        return 'http://www.jinzht.com/static/app/img/%s' %(default or 'icon.png')
    #if not file: return '%s/media/default/coremember.png' % settings.DOMAIN
    return '%s%s' % (settings.DOMAIN, file.url)


def info(user):
    if not user.name or not user.idno or not user.company or not user.position or not user.addr:
        return False
    return True

@api_view(['POST'])
def openid(req):
    openid = req.data.get('openid', '').strip()
    print(openid)
    if not openid:
        return r(1, '微信不能为空')
    user = User.objects.filter(openid=openid)
    return r_(0, {'flag': user.exists()})
        

@api_view(['POST'])
def sendcode(req, flag, weixin):
    tel = req.data.get('tel')
    if not valtel(tel): 
        return r(1, '手机格式不正确')
    is_new_user = False # 是否全新注册, 默认为 False
    if weixin == '1':
        if flag == '1':
            return r(1, 'debug')
        openid = req.data.get('openid')
        if not openid:
            return r(1, '微信不能为空')
        if not User.objects.filter(Q(openid=openid) | Q(tel=tel)).exists(): # 全新注册
            is_new_user = True 
        elif User.objects.filter(openid=openid, tel=tel).exists(): # 用户存在
            return r(1, '用户已经存在, 请直接登录')
    elif weixin == '0':
        user = User.objects.filter(tel=tel)
        if flag == '0' and user.exists():
            return r(1, '该手机已注册, 请直接登录')
        elif flag == '1' and not user.exists():
            return r(1, '您尚未注册, 请先注册')

    code = SMS(tel).send() # 验证码
    print(code)
    if not code: 
        return r(-1, '获取验证码失败')

    req.session.set_expiry(60 * 10)
    req.session[tel] = code
    req.session.set_expiry(3600 * 24)
    #req.session.set_expiry(3)
    return r_(0, {'flag': is_new_user}, '验证码已发送, 请耐心等待')


@api_view(['POST'])
def registe(req, os):
    tel = req.data.get('tel')
    code = req.data.get('code')
    regid = req.data.get('regid', '')
    passwd = req.data.get('passwd')
    sode = req.session.get(tel)
    version = '1'

    if not valtel(tel):
        return r(1, '手机格式不正确')
    if not sode:
        return r(1, '请先获取验证码')
    if not regid: 
        return r(1, 'regid')
    if code != str(sode):
        return r(1, '验证码错误')

    if 'openid' in req.data:
        openid = req.data.get('openid').strip()
        nickname = req.data.get('nickname', '').rstrip()
        print(nickname, '---------------')
        photo = req.data.get('file')
        if not openid:
            return r(1, '微信不能为空')

        openid_user = User.objects.filter(openid=openid)
        if not openid_user.exists(): # openid 不存在
            tel_user = User.objects.filter(tel=tel)

            if not tel_user.exists(): # 全新创建 
                if not passwd:
                    return r(1, '请输入密码')
                print('a')
                user = User.objects.create(
                    openid=openid, 
                    nickname = nickname,
                    photo = photo,
                    tel=tel, 
                    passwd=passwd,
                    os=int(os), 
                    regid=regid, 
                    version = version
                ) 
            else: # 给手机绑定 openid 
                print('b')
                user = tel_user[0]
                user.openid = openid
                user.nickname = nickname
                user.os = int(os)
                user.regid = regid
                user.version = version
                store(user.photo, photo)
                user.save()
        else: # openid 存在
            user = openid_user[0]
            if not tel == user.tel:
                print('c')
                tel_user = User.objects.filter(tel=tel)
                if tel_user.exists(): # 给确定手机绑定 openid
                    print('d')
                    user.openid = ''
                    user.save()

                    user = tel_user[0]
                    user.openid = openid
                    user.nickname = user.nickname
                    user.regid = regid
                    user.version = version
                    user.os = int(os)
                    store(user.photo, photo)
                    user.save()
                else: # 给某个openid换绑手机
                    print('e')
                    user.tel = tel
                    user.regid = regid
                    user.version = version
                    user.os = int(os)
                    user.save()
    else:
        print('f')
        if not passwd:
            return r(1, '请输入密码')
        if User.objects.filter(tel=tel).exists(): 
            return r(1, '您的手机号码已注册, 请直接登录')
        user = User.objects.create(
            tel=tel, 
            passwd=passwd, 
            os=int(os),
            regid = regid,
            version = version
        ) 

    req.session[tel] = ''
    req.session.set_expiry(3600 * 24)
    req.session['uid'] = user.id
    data = {'auth': is_auth(user), 'info': info(user)}
    return r_(0, data)

def is_auth(user):
    if user.valid == True:
        return True
    if user.valid == False:
        return False
    if not user.qualification:
        return ''
    return None

@api_view(['GET'])
@login()
def myauth(req):
    user = u(req)
    data = {'auth': is_auth(user)}
    return r_(0, data)
@api_view(['POST'])
def login_(req):
    regid = req.data.get('regid', '').strip()
    if not regid:
        return r(1, 'debug')

    if 'openid' in req.data:
        openid = req.data.get('openid').strip()
        if not openid:
            return r(1, 'openid不能为空')
        user = User.objects.filter(openid=openid)
        if user.exists():
            user = user[0]
        else:
            return r(1, '请先绑定微信')
    else:
        tel = req.data.get('tel')
        passwd = req.data.get('passwd')
        if not valtel(tel): 
            print(tel, type(tel))
            return r(1, '手机格式不正确')

        user = User.objects.filter(tel=tel)
        if user.exists():
            user = user[0]
            if not passwd == user.passwd:
                return r(1, '手机号码或密码错误')
        else:
            return r(1, '您尚未注册, 请先注册')
    #-------------------------------------------#
    req.session.set_expiry(3600 * 24)
    #req.session.set_expiry(3)
    req.session['uid'] = user.id 
    user.regid = regid
    user.lastlogin = timezone.now()
    user.save()
    data = {'auth': is_auth(user), 'info': info(user)}
    print(data)
    return r_(0, data, '登录成功')


@api_view(['GET'])
def logout(req):

    req.session['uid'] = ''
    return r(0, '退出成功')


@api_view(['POST'])
def resetpasswd(req):
    tel = req.data.get('tel')
    code = req.data.get('code')
    passwd = req.data.get('passwd')

    if not valtel(tel): 
        return r(1, '手机格式不正确')
    if not passwd:
        return r(1, '密码不能为空')

    sode = req.session.get(tel)
    if not sode:
        return r(1, '请先获取验证码')

    user = User.objects.get(tel=tel) 
    #if not user.exists(): 
    #    return r(1, '您尚未注册, 请先注册')
    if code != str(sode): 
        return r(1, '验证码错误')

    user.passwd = passwd
    user.save()

    req.session.set_expiry(3600 * 24)
    req.session['uid'] = user.id
    req.session[tel] = ''
    return r(0, '设置密码成功')


@api_view(['POST'])
@login()
def modifypasswd(req):
    user = u(req)
    old = req.data.get('old')
    new = req.data.get('new')

    if not new:
        return r(1, '新密码不能为空')
    print(old)
    if old != user.passwd: 
        return r(1, '旧密码输入有误')

    user.passwd = new
    user.save()
    return r(0, '修改密码成功')

            
@api_view(['POST'])
@login()
def weixin(req):
    weixin = req.data.get('weixin','').strip()
    if not weixin: 
        return r(1, '微信')
    user = User.objects.get(pk=req.session.get('uid'))
    user.weixin = weixin; user.save()
    return r(0, '微信设置成功')

def stage(project):
    now = timezone.now()
    if not project.start:
        stage = {
            'flag': 1,
            'code': '路演预告',
            'color': 0xE69781,
            'start': {
                'name': '路演时间',
                'datetime': '待定',
            },
            'end': {
                'name': '报名截止',
                'datetime': '待定'
            }
        }
    elif now < project.start: # 现在时间 < 路演开始时间
        stage = { 
                    'flag': 1,
                    'code': '路演预告', 
                    'color': 0xE69781,
                    'start': {
                        'name':'路演时间', 
                        'datetime':dateformat(project.start)
                        },
                    'end': {
                        'name':'报名截止', 
                        'datetime': dateformat(project.start- timedelta(days=2))
                        }
                }

    elif now > project.stop:
        if now > project.stop:
            stage = {
                    'flag': 3,
                    'code': '融资完毕', 
                    'color': 0xDC471C,
                    'start': {
                        'name': '众筹时间', 
                        'datetime': dateformat(project.start),
                    },
                    'end': {
                        'name': '截止时间', 
                        'datetime': dateformat(project.stop)
                    }
                }
        else:
            stage = {
                    'flag': 2,
                    'code': '融资进行', 
                    'color': 0xD4A225,
                    'start': {
                        'name': '众筹时间', 
                        'datetime': dateformat(project.start),
                    },
                    'end': {
                        'name': '截止时间', 
                        'datetime': dateformat(project.stop)
                    }
                }
    else:
            stage = {
                    'flag': 2,
                    'code': '融资进行', 
                    'color': 0xD4A225,
                    'start': {
                        'name': '众筹时间', 
                        'datetime': dateformat(project.start),
                    },
                    'end': {
                        'name': '截止时间', 
                        'datetime': dateformat(project.stop)
                    }
                }
    return stage


def _finance(queryset, page):
    size = settings.DEFAULT_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        data.append({
            'id': item.id,
            'img': img(item.img),
            'company': item.company.name,
            'abbrevcompany': re.sub(r'(股份)?有限(责任)?公司', '', item.company.name),
            'addr': item.company.addr,
            'tag': item.tag,
            'date': dateformat(item.start),
        }) 
    if len(queryset) < size:
        return r_(2, data, '加载完毕')
    else:
        return r_(0, data)

def _financing(queryset, page):
    size = settings.DEFAULT_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        _queryset = Invest.objects.filter(project=item, valid=True)
        tmp = _queryset.aggregate( amount_sum=Coalesce(Sum('amount'), Value(0)) )['amount_sum']
        invest = tmp + int(item.finance2get)
        investor = _queryset.count()
        data.append({
            'id': item.id,
            'img': img(item.img),
            'company': re.sub(r'(股份)?有限(责任)?公司', '', item.company.name),
            'planfinance': item.planfinance,
            'invest': invest,    
            'investor': investor,
            'date': dateformat(item.stop),
        }) 
    if len(queryset) < size:
        return r_(2, data, '加载完毕')
    else:
        return r_(0, data)

def _financed(queryset, page):
    size = settings.DEFAULT_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        _queryset = Invest.objects.filter(project=item, valid=True)
        invest = item.finance2get
        investor = _queryset.count()
        data.append({
            'id': item.id,
            'img': img(item.img),
            'company': re.sub(r'(股份)?有限(责任)?公司', '', item.company.name),
            'planfinance': item.planfinance,
            'invest': invest,    
            'investor': investor,
            'date': dateformat(item.stop),
        }) 
    if len(queryset) < size:
        return r_(2, data, '加载完毕')
    else:
        return r_(0, data)

def _upload(queryset, page):
    size = settings.DEFAULT_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        data.append({
            'id': img(item.id),
            'img': img(item.img),
            #'name': item.user.name,
            #'tel': item.user.tel,
            'company': item.company,
            'abbrevcompany': re.sub(r'(股份)?有限(责任)?公司', '', item.company),
            #'desc': item.desc,
            #'vcr': createurl(item.vcr),
            'date': dateformat(item.create_datetime)
        })
    code = 2 if len(data) < size else 0
    return r_(code, data)

@api_view(['GET'])
@login()
def cursor(req):
    return r_(0, data={'cursor': settings.CURSOR})

@api_view(['GET'])
def project(req, cursor, page):
    cursor = int(cursor)
    if cursor == 0:
        cursor = settings.CURSOR # 默认显示
    #---------- 根据cursor返回不同的值-----------#
    now = timezone.now()
    if cursor == 1:
        queryset = Project.objects.filter(Q(start__isnull=True) | Q(start__gt=now))
        return _finance(queryset, page)
    elif cursor == 2:
        queryset = Project.objects.filter(start__lte=now, stop__gte=now)
        return  _financing(queryset, page)
    elif cursor == 3:
        queryset = Project.objects.filter(start__isnull=False, stop__lt=now)
        return  _financed(queryset, page)
    else:
        queryset = Upload.objects.filter(valid=True)
        return  _upload(queryset, page)
    #--------- End cursor ----------------------#

@api_view(['GET'])
def thinktankdetail(req, pk):
    item = i(Thinktank, pk)
    if not item: 
        return ENTITY
    data = {
        'signature': item.signature,
        'video': item.video,
        'experience': item.experience,
        'cases': item.case,
        'domain': item.domain,
    }
    return Response({'code':0, 'msg':'', 'data':data})
    
@api_view(['GET'])    
def thinktank(req, page):
    size = settings.DEFAULT_PAGESIZE
    queryset = q(Thinktank.objects.all(), page, size)
    data = list()
    for item in queryset:
        data.append({
            'id': item.id,
            'photo': img(item.photo),
            'name': item.name,
            'company': item.company,
            'position': item.position,
        })
    if len(queryset) < size:
        return r_(2, data, '加载完毕')
    else:
        return r_(0, data)

def amountsum(flag, project):
    if flag == 1: 
        return 0
    elif flag == 2:
        tmp = Invest.objects.filter(project=project, valid=True).aggregate(Sum('amount'))['amount__sum']
        if not tmp: tmp = 0 
        return (tmp + int(project.finance2get))
    else: 
        return project.finance2get

@api_view(['GET'])
@login()
def projectdetail(req, pk):
    item = i(Project, pk)
    if not item:
        return ENTITY

    stg = stage(item)
    user = u(req)
    data = {
        'id': item.id,
        'company': item.company.name,
        'stage': stg,
        'planfinance': item.planfinance,
        'img': img(item.img),
        'video': item.video or createurl(item.upload.vcr if item.upload else ''),
        'profile': '    ' + item.company.profile,
        'business': '    ' + item.business,
        'model': '    ' + item.model,
        'invest': amountsum(stg['flag'], item),
        'is_like': user in item.like.all(),
        'is_collect': user in item.collect.all(),
        'is_attend': user in item.attend.all(),
        'like': item.like.all().count(),
        'collect': item.collect.all().count(),
        'minfund': item.minfund,
        'event': item.event,
    }
    return r_(0, data)

@api_view(['GET'])
@login()
def uploaddetail(req, pk):
    item = i(Upload, pk)
    if not item:
        return ENTITY
    data = {
        'planfinance': item.planfinance,
        'profile': item.profile,
        'business': item.business,
        'model': item.model,
    }

@api_view(['GET'])
def financeplan(req, pk):
    item = i(Project, pk)
    if not item: 
        return ENTITY
    user = u(req)
    share2givevalue =user.os==1 and item.share2give/100 or item.share2give
    print ("here is %d"% share2givevalue)
    data = {
        'planfinance': item.planfinance,
        'share2give':share2givevalue,
        'usage': item.usage,
        'quitway': item.quitway,
        'minfund': item.minfund,
    }
    return r_(0, data)

@api_view(['GET'])
@login()
def member(req, pk):
    project = i(Project, pk)
    if not project: 
        return ENTITY
    data = list()
    for item in project.member_set.all():
        data.insert(0, {
            'id': item.id,
            'photo': img(item.photo),
            'name': item.name,
            'position': item.position,
            'profile': item.profile,
        })
    return r_(2, data)


@api_view(['GET'])
def investlist(req, pk):
    queryset = Invest.objects.filter(project__pk=pk, valid=True)
    data = list()
    for item in queryset:
        user = item.user
        data.append({
            'amount': item.amount,
            'name': user.name or user.tel[-4:],
            'photo': img(user.photo),
            'date': dateformat(item.create_datetime),
        })
    return r_(2, data)

@api_view(['GET'])
@login()
def attend(req, pk):
    project = i(Project, pk)
    if not project: 
        return ENTITY
    user = u(req)
    if user in project.attend.all(): 
        return r(1, '您已申请参加该项目, 无需重复报名')
    project.attend.add(user)
    return r(0, '恭喜您, 申请成功')

def _auth(queryset, page):
    size = settings.DEFAULT_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        data.append({
            'id': item.id,
            'name': item.name,
            'photo': img(item.img),
            'company': item.company,
            'position': item.position,
            'date': dateformat(item.create_datetime),
        }) 
    if len(queryset) < size:
        return r_(2, data, '加载完毕')
    else:
        return r_(0, data)

@api_view(['GET'])
def authdetail(req, pk):
    item = i(User, pk)
    if not item:
        return ENTITY
    data = {
        'profile': item.profile,
        'signature': item.signature,
        'investplan': item.investplan,
        'investcase': item.investcase,
    }
    return r_(0, data)

def _institute(queryset, page):
    size = settings.DEFAULT_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        data.append({
            'id': item.id,
            'logo': img(item.logo),
            'abbrevname': re.sub(r'(股份)?有限(责任)?公司', '', item.name),
            'name': item.name,
            'addr': item.addr,
        }) 
    if len(queryset) < size:
        return r_(2, data, '加载完毕')
    else:
        return r_(0, data)

@api_view(['GET'])
def institutedetail(req, pk):
    item = i(Institute, pk)
    if not item:
        return ENTITY
    data = {
        'foundingtime': item.foundingtime,
        'homepage': item.homepage,
        'profile': item.profile,
        'fundsize': item.fundsize,
        'investcase': [{'company': i.company, 'logo': img(i.logo)} for i in item.investcase.all()],
    }
    return r_(0, data)

@api_view(['GET'])
@login()
def investor(req, cursor, page):
    cursor = int(cursor)
    if cursor == 0:
        cursor = settings.CURSOR # 默认显示
    
    if cursor == 1:
        queryset = User.objects.filter(valid=True)
        return _auth(queryset, page)
    if cursor == 2:
        queryset = Institute.objects.all()
        return _institute(queryset, page)

@api_view(['POST'])
@login()
def upload(req):
    user = u(req)
    if Upload.objects.filter(~Q(valid=True), user=user).exists(): 
        return r(1, '您还有项目尚在审核中')
    company = req.data.get('company', '').strip()
    desc = req.data.get('desc', '').strip()
    vcr = req.data.get('vcr')

    if not company:
        return r(1, '公司不能为空')
    if not desc:
        return r(1, '项目描述不能为空')
    if not vcr:
        return r(1, 'vcr不能为空')

    obj = Upload.objects.create(
        user=user, 
        company=company, 
        desc = desc,
        vcr = vcr,
    )
    return r(0, '您的项目已成功入选项目库')

@api_view(['GET'])
@login()
def leftslide(req):
    user = u(req) 
    data = {
        'photo': img(user.photo), 
        'nickname': user.nickname or '未设置' 
    } 
    return r_(0, data)

@api_view(['POST'])
@login()
def photo(req):
    photo = req.data.get('file')
    if not photo:
        return r(1, '图像不能为空')    

    user = u(req)
    flag = store(user.photo, photo)
    if not flag: 
        return r(1, '图像设置失败')
    return r(0, '图像设置成功')

@api_view(['GET', 'POST'])
@login()
def bg(req):
    if req.method == 'GET':
        user = u(req)
        data = {
            'bg': img(user.bg, 'feeling.png'), 
            'photo': img(user.photo)
        }
        return r_(0, data)
    elif req.method == 'POST':
        bg = req.data.get('file')
        if not bg:
            return r(1, '图像不能为空')    

        user = u(req)
        flag = store(user.bg, bg)
        if not flag:
            return r(1, '设置背景失败') 
        return r(0, '设置背景成功')

@api_view(['POST'])
@login()
def nickname(req):
    nickname = req.data.get('nickname', '').rstrip()
    if not nickname:
        return r(1, '昵称不能为空')
    user = u(req) 
    user.nickname = nickname
    user.save()
    return r(0, '昵称设置成功')


@api_view(['POST'])
@login()
def company(req):
    company = req.data.get('company', '').strip()
    if not company:
        return r(1, '公司不能为空')

    user = u(req)
    user.company = company
    user.save()
    return r(0, '公司设置成功')


@api_view(['POST'])
@login()
def position(req):

    position = req.data.get('position', '').strip()
    if not position:
        return r(1, '职位不能为空')

    user = u(req)
    user.position = position
    user.save()
    return r(0, '职位设置成功')


@api_view(['POST'])
@login()
def addr(req):
    addr = req.data.get('addr', '').strip()
    if not addr:
        return r(1, '地址不能为空')

    user = u(req)
    user.addr = addr
    user.save()
    return r(0)

@api_view(['GET'])
@login()
def customservice(req):
    data = settings.CUSTOMSERVICE
    return r_(0, data)

@api_view(['GET'])
@login()
def home(req):
    queryset= Banner.objects.reverse()[:4]
    banner = list()
    for item in queryset:
        banner.append({
            'img': img(item.img),
            'project': item.project.id if item.project else None,
            'url': item.url
        })
    size = settings.DEFAULT_PAGESIZE
    now = timezone.now()
    #rcmd=True
    #queryset = Project.objects.filter(
    #    start__lte=now, 
    #    stop__gte=now,
    #)
    queryset = Project.objects.all()[:4]
    queryset = q(queryset, 0, size)
    project = list()
    for item in queryset:
        tmp = Invest.objects.filter(project=item, valid=True).aggregate(Sum('amount'))['amount__sum']
        if not tmp: tmp = 0 
        invest = tmp + int(item.finance2get)
        project.append({
            'id': item.id,
            'img': img(item.img),
            'company': re.sub(r'(股份)?有限(责任)?公司', '', item.company.name),
            'tag': item.tag,
            'planfinance': item.planfinance,
            'invest': invest,
            'date': dateformat(item.stop),
        }) 
    
    data = {
        'banner': banner,
        'announcement': {
            'title': '新手指南', 
            'url': '%s/phone/annc/user_guide/' %(settings.DOMAIN),
            #'url': img(None, 'new_user_guide.png') #'http://www.jinzht.com'
        },
        'project': project,
        'platform': [
            {'key': '成功融资总额(元)', 'value': '56125895423'},
            {'key': '项目总数', 'value': '451231'},
            #{'key': '投资人总人数', 'value': '254566'},
            #{'key': '基金池总额(元)', 'value': '452122553144'},
        ],
    }
    return r_(0, data)    


@api_view(['POST', 'GET'])
#@login()
def credit(req):
    if req.method == 'GET':
        queryset = random.sample(list(Company.objects.all()), 5)
        data = {'company': [ c.name for c in queryset ]}
    else:
        from phone.sanban18 import Credit
        wd = req.data.get('wd', '').strip()
        if not wd:
            return r(1, '关键词不能为空')

        data = Credit().outcome(wd)
    return r_(0, data)


@api_view(['POST'])
@login()
def name(req):
    user = u(req)
    if is_auth(user) == True:
        return r(1, '您已认证, 姓名不能修改')
    name = req.data.get('name')
    if not name:
        return r(1, '姓名不能为空')

    user.name = name
    user.save()
    return r(0, '姓名修改成功')


@api_view(['GET', 'POST'])
@login()
def userinfo(req, uid=None):
    if req.method == 'GET':
        uid = uid or s(req)
        user = i(User, uid)
        if not user:
            return r(1, 'debug') 
        data = { 
            'uid': s(req),
            'tel': user.tel,
            'gender': user.gender,
            'photo': img(user.photo),
            'nickname': user.nickname,
            'name': user.name,
            'idno': user.idno,
            'idpic': img(user.idpic),
            'company': user.company,
            'position': user.position,
            'addr': user.addr}
        return r_(0, data)

    elif req.method == 'POST':
        user = u(req)
        if user.valid == True:
            return r(1, '信息已被核实, 更改请联系客服')
        name = req.data.get('name', '').strip() 
        idno = req.data.get('idno', '').strip()
        company = req.data.get('company', '').strip()
        position = req.data.get('position', '').strip()
        addr = req.data.get('addr', '').strip()

        if not name:
            return r(1, '姓名不能为空')
        if not company:
            return r(1, '公司不能为空')
        if not position:
            return r(1, '职位不能为空')
        if not addr:
            return r(1, '地址不能为空')
        if not idno:
            return r(1, '身份证不能为空')

        from phone.idno import IDNO
        flag, info = IDNO(idno).ip138() 
        if not flag:
            return r(1, info)
        gender = info['gender']
        birthday = info['birthday']
        birthplace = info['birthplace']

        addr = addr.replace('省', '').replace('市', '').replace('区', '')
        addr = re.sub(r' {2,}', ' ', addr)
        
        ret = (name, idno, company, position, addr, gender, birthday, birthplace)
        user.name = name
        user.idno = idno
        user.company = company
        user.position = position
        user.addr = addr
        user.gender = gender
        user.birthday = birthday
        user.birthplace = birthplace
        user.save()

        print(ret)
        return r(0)

@api_view(['GET', 'POST'])
@login()
def auth(req):
    user = u(req)

    if req.method == 'GET':
        qualification = [{'key': i[0], 'value': i[1]} for i in QUALIFICATION]
        data = {
                'idpic': '%s%s' %(settings.DOMAIN, user.idpic.url) if user.idpic else '',  
                'qua': user.qualification,
                'institute': user.comment.split(';')[0],
                'legalperson': user.comment.split(';')[-1],
                'company': user.company, 
                'position': user.position, 
                'qualification': qualification,
                'industry': INDUSTRY
        }
        return r_(0, data)

    elif req.method == 'POST':
        _auth = is_auth(user)
        if info(user) == False:
            return r(1, '请先完善个人信息, 然后认证')
        if _auth == True:
            return r(1, '认证成功, 更改请联系客服')
        elif _auth == False:
            return r(1, '认证失败, 更改请联系客服')
        is_institute = 'institute' in req.data # 机构认证
        qualification = req.data.get('qualification', '').strip()
        qualification = set(qualification.split(','))
        choice = set(str(item[0]) for item in QUALIFICATION)
        idpic = req.data.get('idpic')
        if not is_institute:
            img = req.data.get('img')
            if not img:
                return r(1, '投资人图像未上传')

        if not qualification or not qualification <= choice:
            return r(1, '认证资格有误')
        if not idpic:
            return r(1, '身份证未上传')
        
        investfield = investscale = profile = comment = ''
        if is_institute: # 机构认证
            institute = req.data.get('institute', '').strip().replace(';', '')
            legalperson = req.data.get('legalperson', '').strip().replace(';', '')
            fundsize = req.data.get('fundsize', '').strip()
            
            if not institute or not CHINESE_RE.match(institute):
                return r(1, '机构输入有误')
            if not legalperson or not CHINESE_RE.match(institute):
                return r(1, '法人输入有误')

            comment = '%s;%s;%s' % (institute, legalperson, fundsize)
        else:
           investfield = req.data.get('investfield', '').strip()
           investscale = req.data.get('investscale', '').strip()
           profile = req.data.get('profile', '').strip()
        
        user.qualification = ','.join(sorted(qualification))
        user.investfield = investfield
        user.investscale = investscale
        user.profile = profile
        user.comment = comment
        user.save()
        flag = store(user.idpic, idpic)
        if not flag:
            return r(1, '上传身份证失败')
        if not is_institute:
            flag = store(user.img, img)
            if not flag:
                return r(1, '上传图像失败')
        return r(0, '认证提交成功') 

def _like(item, user, flag):
    if not item:
        return ENTITY
    if flag == '0':
        item.like.add(user)
        return r_(0, {'is_like': True})
    else:
        item.like.remove(user)
        return r_(0, {'is_like': False})

@api_view(['GET'])
@login()
def projectlike(req, pk, flag):
    return _like(i(Project, pk), u(req), flag)

@api_view(['GET']) 
def uploadlike(req, pk, flag):
    return _like(i(Upload, pk), u(req), flag)

def _collect(item, user, flag):
    if not item:
        return ENTITY
    if flag == '0':
        item.collect.add(user)
        return r_(0, {'is_collect': True})
    else:
        item.collect.remove(user)
        return r_(0, {'is_collect': False})

@api_view(['GET'])
@login()
def projectcollect(req, pk, flag):
    return _collect(i(Project, pk), u(req), flag)

@api_view(['GET'])
@login()
def uploadcollect(req, pk, flag):
    return _collect(i(Upload, pk), u(req), flag)

@api_view(['GET'])
@login()
def collectfinancing(req, page):
    now = timezone.now()
    queryset = Project.objects.filter(
        collect=u(req),
        start__lte=now, 
        stop__gte=now,
    )
    return __collect(queryset, page)

@api_view(['GET'])
@login()
def collectfinanced(req, page):
    queryset = Project.objects.filter(
        collect=u(req),
        stop__lt=timezone.now()
    )
    return __collect(queryset, page)

def __collect(queryset, page):
    size = settings.DEFAULT_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        data.append({
            'id': item.id,
            'img': img(item.img),
            'company': item.company.name,
            'start': dateformat(item.start),
            'stop': dateformat(item.stop),
        })
    if len(queryset) < size:
        return r_(2, data, '加载完毕')
    else:
        return r_(0, data)

@api_view(['GET'])
@login()
def collectfinance(req, page):
    now = timezone.now()
    queryset = Project.objects.filter( 
        Q(start__isnull=True) | 
        Q(start__gt=now),
        collect=u(req)
    )
    return __collect(queryset, page)

@api_view(['POST', 'GET'])
@login()
def feedback(req):
    uid = req.session.get('uid')
    advice = req.data.get('advice', '').strip()
    MAIL('反馈', advice).send()
    return r(0, '反馈成功')

@api_view(['GET'])
def keyword(req):
    data = {'keyword': INDUSTRY}
    return r_(0, data)

def __project(queryset, page):
    size = settings.DEFAULT_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        data.append({
            'id': item.id,
            'img': img(item.img),
            'company': item.company.name,
            'profile': item.company.profile,
            'start': dateformat(item.start),
            'stop': dateformat(item.stop),
        })
    if len(queryset) < size:
        return r_(2, data, '加载完毕')
    else:
        return r_(0, data)

@api_view(['POST'])
def projectsearch(req, page):
    value = req.data.get('wd', '').strip()
    if not value: 
        return r(1, '输入不能为空')
    queryset = Project.objects.filter(Q(tag__contains=value)|Q(company__name__contains=value)).distinct()
    return __project(queryset, page)


@api_view(['POST'])
@login()
def wantinvest(req, pk, flag):
    amount = req.data.get('amount', '').strip() # 投资金额
    if not PK_RE.match(amount): 
        return r(1, '非法输入')
    project = i(Project, pk) # 项目
    if not project: 
        return ENTITY
    fund = project.minfund
    if int(amount) < fund:
        return r_(1, {'flag': False},  '金额必须大于%s万' % fund)
    user = u(req)
    invest = Invest.objects.filter(project=project, user=user) #是否投资过
    if invest.exists():
        return r(1, '您已投资过该项目')
    Invest.objects.create(
        user = user,
        project = project,
        amount = amount,
        lead = flag
    )
    return r(0, '投资信息提交成功')

@api_view(['GET'])
@login()
def myupload(req, page):
    queryset = Upload.objects.filter(user=u(req))
    return _upload(queryset, page)

@api_view(['GET'])
@login()
def myinvest(req, page):
    queryset = Invest.objects.filter(user=u(req))
    return __collect(queryset, page)

@api_view(['POST', 'GET'])
@login()
def token(req):
    user = u(req)
    if req.method == 'GET':
        if Upload.objects.filter(~Q(valid=True), user=user).exists():
            return r(1, '您还有项目尚在审核中')
        else:
            return r(0)
    else:
        key = req.data.get('key', '').strip()
        if not key:
            return r(1, '上传视频名不能为空')
        if Upload.objects.filter(~Q(valid=True), user=user).exists():
            return r(1, '您还有项目尚在审核中')

        q = Auth(settings.AK, settings.SK)
        token = q.upload_token(settings.BN, key)
        token2 = q.upload_token(settings.BN, key, 7200, {'callbackUrl':'%s/phone/callback/' % settings.DOMAIN, 
            'callbackBody':'name=$(fname)&hash=$(etag)'})
        data = {'token': token2}
        return r_(0, data)

def createurl(name):
    if not name: return ''
    q = Auth(settings.AK, settings.SK)
    url = 'http://%s/%s' % (settings.BD, name)
    url = q.private_download_url(url, expires=3600)
    print(url)
    return url

@api_view(['POST'])
@login()
def callback(req):
    name = req.data.get('name', '').strip()
    if not name: 
        return r(1, '视频名不能为空')
    print('name')
    url = createurl(name)
    data = {'url': url}
    return r_(0, data,  '视频上传成功')

    
@api_view(['POST'])
@login()
def delvideo(req):
    key = req.data.get('key','').strip()
    if not key: return r(1, '参数错误')
    q = Auth(settings.AK, settings.SK)
    bucket = BucketManager(q)
    ret, info = bucket.delete(settings.BN, key)
    if ret is None and info.status_code == 612:
        return r(0, '删除视频成功')
    else:
        return r(1, '删除视频失败')
    #assert ret is None
    #assert info.status_code == 612

@api_view(['POST', 'GET'])
@login()
def ismyproject(req, pk):
    project = i(Project, pk)
    if not project: return ENTITY
    uid = req.session.get('uid')
    if project.roadshow and  project.roadshow.user.id == uid: 
        return r(1, '你不可以给自己的项目投资哦')
    return r(0, '')


@api_view(['GET'])
@login()
def valsession(req):
    return r(0)

@api_view(['POST', 'GET'])
def checkupdate(req, os):
    return r(1, '没有更新')
    data = {
        'force': False, #True,
        'edition': '2.1.0',
        'item': '1,更改投融资\n2,开启上传项目\n3,增加圈子功能',
        #'href': 'http://a.app.qq.com/o/simple.jsp?pkgname=com.jinzht.pro',
        'href': 'http://dd.myapp.com/16891/274E705CD88A17A68B682C2F944742AF.apk?fsname=com.jinzht.pro_2.0.6_10.apk&amp;asr=02f1',
    }
    return r_(0, data)

@api_view(['POST', 'GET'])
def shareproject(req, pk):
    data = dict()
    data['title'] = '项目分享'
    data['img'] = 'http://www.jinzht.com/static/app/img/icon.png' #% settings.DOMAIN
    data['url'] = 'http://a.app.qq.com/o/simple.jsp?pkgname=com.jinzht.pro'
    data['content'] = '项目分享'
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def shareapp(req):
    data = dict()
    data['title'] = '金指投科技'
    data['img'] = 'http://www.jinzht.com/static/app/img/icon.png' #% settings.DOMAIN
    data['url'] = 'http://a.app.qq.com/o/simple.jsp?pkgname=com.jinzht.pro'
    data['content'] = '金指投App分享'
    return Response({'code':0, 'msg':'', 'data':data})

def document(name):
    cur_dir = os.path.dirname(__file__)
    f = os.path.join(cur_dir, 'document/%s' %name )
    if not os.path.exists(f):
        return r(1, 'no data')

    import codecs
    with codecs.open(f, 'r', 'utf-8') as fp:
        data = fp.read()
        return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def privacy(req):
    return document('privacy')

@api_view(['POST', 'GET'])
def aboutroadshow(req):
    return document('aboutroadshow')

@api_view(['GET'])
def risk(req):
    return document('risk')

@api_view(['POST', 'GET'])
def useragreement(req):
    return document('useragreement')

@api_view(['POST', 'GET'])
def projectprotocol(req):
    return document('projectprotocol')

@api_view(['POST', 'GET'])
def crowfunding(req):
    return document('crowfunding')

@api_view(['POST', 'GET'])
def leadfunding(req):
    return document('leadfunding')

@api_view(['POST'])
@login()
def topic(req, pk):
    content = req.data.get('content','').rstrip()
    if not content: 
        return r(1, '内容不能为空')

    project = i(Project, pk)
    if not project: 
        return ENTITY

    at = req.data.get('at', 0)
    if not at: 
        at, msg = None, '发表话题成功'
    else: 
        at, msg = i(Topic, at), '回复成功'

    user = u(req)
    if at and at.user == user:
        return r(1, '不能给自己回复哦')

    obj = Topic.objects.create(
       project = project,
       user = user,
       at = at,
       content = content,
    )
    return r_(0, {'id': obj.id}, msg)

def __topiclist(queryset, page):
    size = settings.TOPIC_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        tmp = dict()
        tmp['pid'] = item.project.id
        tmp['id'] = item.id
        tmp['photo'] = img(item.user.photo)
        tmp['name'] = item.user.name or item.user.tel[-4:]
        if item.at: 
            tmp['at_name'] = item.at.user.name or item.at.user.tel[-4:]
        tmp['date'] = dt_(item.create_datetime) 
        tmp['content'] = item.content
        tmp['auth'] = item.user.valid is True
        data.append(tmp) 
    if len(queryset) < size:
        return r_(2, data, '加载完毕')
    else:
        return r_(0, data)

@api_view(['GET'])
#@login()
def topiclist(req, pk, page):
    queryset = Topic.objects.filter(project__pk=pk)
    return  __topiclist(queryset, page)
   
def __news(queryset, page):
    size = settings.NEWS_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        data.append({
            'id': item.id,
            'title': item.title,
            'src': item.src,
            'content': item.content,
            'img': item.img,
            'create_datetime': dt_(item.create_datetime),
            'read': item.read,
            'share': item.share,
            'url': '%s/%s/%s/' % (settings.DOMAIN, 'phone/sanban', item.name),
        })
    if len(queryset) < size:
        return r_(2, data, '加载完毕')
    else:
        return r_(0, data)

@api_view(['GET'])
def news(req, pk, page):
    queryset = News.objects.filter(newstype__id=pk, valid=True)
    return __news(queryset, page)

def sanban(req, name):
    try:
        return render(req, 'app/sanban/%s' % name)
    except:
        return HttpResponseNotFound('<h1>Page not found</h1>')

def annc(req, name):
    return render(req, 'app/annc/%s.html' % name)

@api_view(['POST', 'GET'])
def sharenews(req, pk):
    news = i(News, pk) 
    if not news: 
        return ENTITY

    data = {
        'img': news.img,
        'url': '%s/%s/%s' %(settings.DOMAIN, 'phone/sanban', news.name),
        'src': news.src,
        'title': news.title,
        'content': news.content,
    }
    return r_(0, data) #Response({'code':0, 'msg':'', 'data':data})

@api_view(['GET'])
def newsshare(req, pk):
    news = i(News, pk) 
    if not news: 
        return ENTITY
    news.share += 1
    news.save()
    return r(0)
        
@api_view(['POST', 'GET'])
def newsread(req, pk):
    news = i(News, pk) 
    if not news:
        return ENTITY
    news.read += 1
    news.save()
    return r(0)
    
@api_view(['POST'])
def newssearch(req, page):
    value = req.data.get('wd', '').strip()
    if not value: 
        return r(1, '输入不能为空')
    queryset = News.objects.filter(title__contains=value)
    return __news(queryset, page)

@api_view(['GET'])
@login()
def newstype(req):
    data = [{'key':item.id, 'value':item.name} for item in NewsType.objects.filter(~Q(valid=False))]
    return r_(0, data)


@api_view(['GET'])
@login()
def hasinform(req): # 有没有系统通知
    queryset = Inform.objects.filter(user=u(req), read=False)
    data = {'count': queryset.count()}
    return r_(0, data)


@api_view(['GET'])
@login()
def inform(req):
    user = u(req)
    queryset = Inform.objects.filter(user=user)
    size = settings.DEFAULT_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        data.append({
            'id': item.id,
            'title': item.push.title,
            'content': item.push.content,
            'create_datetime': timeformat(item.create_datetime),
            'read': item.read,
            'extras':{'api': item.push.pushtype, 'id': item.push.id, 'url': item.push.url}
        })
    return r_(0, data)

@api_view(['GET'])
@login()
def readinform(req, pk):
    inform = i(Inform, pk)
    if not inform:
        return ENTITY
    inform.read = True
    inform.save()
    return r(0)

@api_view(['GET'])
@login()
def deleteinform(req, pk):
    inform = i(Inform, pk)
    if not inform:
        return ENTITY
    user = u(req)
    if inform.user == user:
        inform.delete()
        return r(0)
    return r(1, '不能删除他人评论')


@api_view(['GET'])
@login()
def hastopic(req):
    queryset = Topic.objects.filter(~Q(read=True), at__user=u(req))
    data = {'count': queryset.count()}
    return r_(0, data)

@api_view(['GET'])
@login()
def mytopiclist(req, page):
    user = u(req)
    queryset = Topic.objects.filter(~Q(read=True), at__user=user) 
    ret = __topiclist(queryset, page)
    return ret

@api_view(['POST', 'GET'])
@login()
def readtopic(req, pk):
    topic = i(Topic, pk)
    if not topic: 
        return ENTITY
    topic.read = True 
    topic.save()
    return r(0)

@api_view(['POST', 'GET'])
def latestnewscount(req):
    yesterday = timezone.now() - timedelta(days=1)
    queryset = News.objects.filter(~Q(newstype=4), create_datetime__gt=yesterday)
    return Response({'code':0, 'msg':'', 'data':{'count':queryset.count()}})
    
@api_view(['POST', 'GET'])
def latestknowledgecount(req):
    yesterday = timezone.now() - timedelta(days=1)
    queryset = News.objects.filter(newstype=4, create_datetime__gt=yesterday)
    return Response({'code':0, 'msg':'', 'data':{'count':queryset.count()}})

def __feelinglike(queryset, page, pagesize): 
    queryset = q(queryset, page, pagesize)
    data = list()
    for item in queryset:
        data.append({
            'name': item.name,
            'uid': item.id,
            'photo': img(item.photo),
        })
    return data

def _itemcomment(item, user): # 获取某个人的评论
    dct = {
        'id': item.id,
        'flag': item.user == user,
        'name': item.user.name or item.user.tel[-4:],
        'uid': item.user.id,
        'photo': img(item.user.photo),
        'content': '%s' % (item.content),
    }
    if item.at:
        dct['at_uid'] = item.at.user.id
        dct['at_name'] = item.at.user.name or item.at.user.tel[-4:]
    return dct

def __feelingcomment(queryset, user, page, size):
    queryset = q(queryset, page, size)
    return [_itemcomment(item, user) for item in queryset]
       
def __feeling(item, user): # 获取发表的状态的关联信息
    tmp = { 
        'id': item.id,
        'uid': item.user.id,
        'company': item.user.company,
        'position': item.user.position,
        'addr': item.user.addr,
        'flag': item.user == user,
        'datetime': dt_(item.create_datetime),
        'name': item.user.name or item.user.tel[-4:],
        'photo': img(item.user.photo),
        'content': item.content,
    } 
    news = item.news
    if news: 
        tmp['share'] = {
            'id': news.id,
            'title': news.title, 
            'img': news.img,
            'url': '%s/%s/%s' %(settings.DOMAIN, 'phone/sanban', news.name)
        }
    else:
        tmp['pic'] = [ os.path.join(settings.DOMAIN, v) for v in item.pic.split(';') if v ]

    tmp['is_like'] = user in item.like.all()

    size = settings.FEELINGLIKE_PAGESIZE
    tmp['like'] = __feelinglike(item.like.all(), 0, size)
    tmp['remain_like'] = max(0, item.like.all().count() - size)

    queryset = FeelingComment.objects.filter(feeling=item, valid=None)
    size = settings.FEELINGCOMMENT_PAGESIZE
    tmp['comment'] = __feelingcomment(queryset, user, 0, size)
    tmp['remain_comment'] = max(0, queryset.count() - size)
    return tmp  

@api_view(['GET'])
@login()
def getfeeling(req, pk):
    item = i(Feeling, pk)
    if not item: 
        return ENTITY
    data = __feeling(item, u(req)) 
    return r_(0, data)

@api_view(['GET'])
@login()
def feeling(req, page):
    user = u(req)
    size = settings.FEELING_PAGESIZE
    queryset = q(Feeling.objects.all(), page, size) 
    data = list()
    for item in queryset: 
        data.append( __feeling(item, user) )
    code = 2 if len(queryset) < size else 0
    return r_(code, data)

@api_view(['POST'])
@login()
def postfeeling(req):
    news = req.data.get('news', 0)
    news = i(News, news)
    content = req.data.get('content', '').rstrip()
    relative_path = datetime.now().strftime('media/feeling/%Y/%m')
    absolute_path = os.path.join(settings.BASE_DIR, relative_path)   

    if req.FILES: 
        mkdirp(absolute_path)
    elif not content and not news: 
        return r(1, '发表内容不能为空')

    relative_path_list = list()
    for j, v in enumerate(req.FILES.values()):
        ext = imghdr.what(v)
        if ext not in settings.ALLOW_IMG: 
            return r(1, '图片格式不正确')
        img_name = '{}.{}'.format(uuid.uuid4().hex, ext)
        img = os.path.join(absolute_path, img_name)

        with open(img, 'wb') as fp:
            for data in v.chunks(): 
                fp.write(data)
        relative_path_list.append( os.path.join(relative_path, img_name) )
        if j >= 8 : break

    user = u(req) 
    obj = Feeling.objects.create(
        user = user,
        content = content,
        pic = ';'.join(relative_path_list),
        news = news
    )
    data = __feeling(obj, user) 
    return r_(0, data, '发表成功')

@api_view(['GET'])
@login()
def deletefeeling(req, pk):
    item = i(Feeling, pk)
    if not item: 
        return ENTITY
    user = u(req)
    if item.user == user:
        item.delete()
        return r(0, '删除状态成功')
    return r(1, '不能删除别人的状态')

@api_view(['GET'])
@login()
def likefeeling(req, pk, is_like):
    item = i(Feeling, pk)
    if not item: 
        return ENTITY
    user = u(req) 
    data = { 
        'is_like': not int(is_like),
        'name': user.name,
        'uid': user.id,
        'photo': img(user.photo),
    }
    if is_like == '0': 
        item.like.add(user)
        return r_(0, data)
    else: 
        item.like.remove(user)
        return r_(0, data)

@api_view(['GET'])
@login()
def feelinglikers(req, pk, page):
    item = i(Feeling, pk)
    if not item:
        return ENTITY
    queryset = item.like.all()
    size = settings.FEELINGLIKE_PAGESIZE
    data = __feelinglike(queryset, page, size)
    code = 2 if len(data) < size else 0
    return r_(code, data)

@api_view(['GET'])
@login()
def feelingcomment(req, pk, page):
    item = i(Feeling, pk)
    if not item: return ENTITY
    user = User.objects.get(pk=req.session.get('uid'))
    queryset = Feelingcomment.objects.filter(feeling=item, valid=None)
    size = settings.FEELINGCOMMENT_PAGESIZE
    data = __feelingcomment(queryset, user, page, size)
    code = 2 if len(data) < size else 0 
    return r_(code, data)

@api_view(['POST'])
@login()
def postfeelingcomment(req, pk):
    item = i(Feeling, pk)
    content = req.data.get('content', '').rstrip()
    at = atid = req.data.get('at', None)
    if not item: 
        return ENTITY
    if not content: 
        return r(1, '回复内容不能为空')
    user = u(req)
    if at:
        at = i(FeelingComment, at)
        if at and user == at.user: 
            return r(1, '不能给自己回复哦')
    obj = FeelingComment.objects.create(
        feeling = item,
        user = user,
        content = content,
        at = at
    )
    data = _itemcomment(obj, user)
    return r_(0, data)

@api_view(['GET'])
@login()
def hidefeelingcomment(req, pk):
    item = i(FeelingComment, pk)
    if not item: 
        return ENTITY
    user = u(req)
    if item.user == user:
        item.valid = False; 
        item.save()
        return r(0)
    return r(1, '不能删除别人的评论')

@api_view(['GET'])
@login()
def background(req):
    user = u(req)
    data = {'bg': img(user.bg), 'photo': img(user.photo)}
    return r_(0, data)

@api_view(['GET'])
def test(req):
    url = createurl('wantroadshowe69cac.mp4')
    return r_(0, {'url': url}, 'test')
