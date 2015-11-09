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
#from django.db.models import F, Q, Sum
from collections import OrderedDict
from phone.models import *
from phone.utils import *
import functools
#from PIL import Image as Img
#import StringIO

PK_RE = re.compile(r'^[1-9]\d*$')
MTM_RE = re.compile(r'^[1-9]\d*(,[1-9]\d*)*$')
CHINESE_RE = re.compile(r'[\u4e00-\u9fa5a-zA-Z]+')

NOENTITY = Response({'code': -2, 'msg': '非法操作'})

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
     
    #img = Img.open(StringIO.StringIO(self.image.read()))
    #if img.mode != 'RGB':
    #    img = img.convert('RGB')
    #img.thumbnail((image.width/1.5, image.height/1.5), Img.ANTIALIAS)
    #output = StringIO.StringIO()
    #img.save(output, format='JPEG', quality=70)
    #output.seek(0)
    #image= InMemoryUploadedFile(output,'ImageField', "%s.jpg" %self.image.name.split('.')[0], 'image/jpeg', output.len, None)
    
    ext = imghdr.what(image)
    if ext in ('jpeg', 'png'):
        field.save('file.' + ext, File(image)) 
        return True
    return False

def arg_(field='参数'):
    return Response({'status': ERR, 'msg': '%s' % field})

def img(file, default=''):
    if not file: return '%s/media/default/coremember.png' % settings.DOMAIN
    return '%s%s' % (settings.DOMAIN, file.url)


def info(user):
    if not user.name or not user.idno or not user.company or not user.position or not user.addr:
        return False
    return True

@api_view(['POST'])
def sendcode(req, flag):

    tel = req.data.get('tel')

    if not validtel(tel): 
        return r(1, '手机格式不正确')

    user = User.objects.filter(tel=tel)
    if flag == '0' and user.exists():
        return r(1, '该手机已注册, 请直接登录')
    elif flag == '1' and not user.exists():
        return r(1, '您尚未注册, 请先注册')

    code = SMS(tel).send() # 验证码
    print(code)
    if not code: 
        return r(-1, '获取验证码失败')

    req.session[tel] = code
    req.session.set_expiry(60 * 10)

    return r(0, '验证码已发送, 请耐心等待')

@api_view(['POST'])
def registe(req, os):

    tel = req.data.get('tel')
    code = req.data.get('code')
    passwd = req.data.get('passwd')
    regid = req.data.get('regid', '')
    version = req.data.get('version', '')
    sode = req.session.get(tel)

    if not validtel(tel):
        return r(1, '手机格式不正确')
    if not sode:
        return r(1, '请先获取验证码')
    if not passwd:
        return r(1, '请输入密码')
    if not version: return r(1, 'debug')
    if not regid: return r(1, 'debug')

    if User.objects.filter(tel=tel).exists(): 
        return r(1, '您的手机号码已注册, 请直接登录')
    if code != str(sode):
        return r(1, '验证码错误')

    user = User.objects.create(
        tel=tel, 
        passwd=passwd, 
        os=int(os),
        regid = regid,
        version = version,) 

    req.session[tel] = ''
    req.session['uid'] = user.id
    req.session.set_expiry(3600 * 24)
    return r(0, '注册成功')


@api_view(['POST'])
def login_(req):
    tel = req.data.get('tel')
    passwd = req.data.get('passwd')
    regid = req.data.get('regid', '')
    version = req.data.get('version', '')

    if not validtel(tel): 
        return r(1, '手机格式不正确')

    user = User.objects.filter(tel=tel)
    if user.exists():
        user = user[0]
        if passwd == user.passwd:
            req.session['uid'] = user.id 
            req.session.set_expiry(3600 * 24)
            user.regid = regid
            user.version = version
            user.lastlogin = timezone.now()
            user.save()
            data = {'auth': user.valid, 'info': info(user)}
            return r_(0, data, '登录成功')
        return r(1, '手机号码或密码错误')
    return r(1, '您尚未注册, 请先注册')


@api_view(['GET'])
def logout(req):

    req.session['uid'] = ''
    return r(0, '退出成功')


@api_view(['POST'])
def resetpasswd(req):
    tel = req.data.get('tel')
    code = req.data.get('code')
    passwd = req.data.get('passwd')

    if not validtel(tel): 
        return r(1, '手机格式不正确')
    if not passwd:
        return r(1, '密码不能为空')

    sode = req.session[tel]
    if not sode:
        return r(1, '请先获取验证码')

    user = User.objects.get(tel=tel) 
    #if not user.exists(): 
    #    return r(1, '您尚未注册, 请先注册')
    if code != str(sode): 
        return r(1, '验证码错误')

    user.passwd = passwd
    user.save()

    req.session['uid'] = user.id
    req.session.set_expiry(3600 * 24)
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
    if old != user.passwd: 
        return r(1, '旧密码输入有误')

    user.passwd = new
    user.save()
    return r(0, '修改密码成功')

            
@api_view(['POST'])
@login()
def weixin(req):
    weixin = req.data.get('weixin','').strip()
    if not weixin: return arg_('weixin')
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
            'company': re.sub(r'(股份)?有限(责任)?公司', '', item.company.name),
            'tag': item.tag,
            'date': dateformat(item.start),
        }) 
    code = 2 if len(queryset) < size else 0
    return r_(code, data, '加载完毕')

def _financing(queryset, page):
    size = settings.DEFAULT_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        _queryset = Invest.objects.filter(project=item, valid=True)
        tmp = _queryset.aggregate(Sum('amount'))['amount__sum']
        if not tmp: tmp = 0 
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
    code = 2 if len(queryset) < size else 0
    return r_(code, data, '加载完毕')

def _financed(queryset, page):
    size = settings.DEFAULT_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        _queryset = Invest.objects.filter(project=item, valid=True)
        tmp = _queryset.aggregate(Sum('amount'))['amount__sum']
        if not tmp: tmp = 0 
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
    code = 2 if len(queryset) < size else 0
    return r_(code, data, '加载完毕')

def _preelection(queryset, page):
    size = settings.DEFAULT_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        data.append({
            'name': item.name,
            'tel': item.tel,
            'company': item.company,
            'vcr': create(item.vcr),
        })
    return r_(0, data)

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
        queryset = Project.objects.filter(stop__lt=now)
        return  _financed(queryset, page)
    else:
        queryset = Upload.objects.filter(valid=True)
        return  _preelection(queryset, page)
    #--------- End cursor ----------------------#

@api_view(['GET'])
def thinktankdetail(req, pk):
    item = i(Thinktank, pk)
    if not item: 
        return r(-2, '系统错误')
    data = {
        'video': item.video,
        'experience': item.experience,
        'case': item.case,
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
    code = 2 if len(queryset) < size else 0
    return r_(code, data, '加载完毕')

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
        return r(-2, '系统错误')

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
        'is_collect': Collect.objects.filter(user=user, project=item).exists(), #item.collect_set.all().filter(user=user).exists(),
        'is_attend': user in item.attend.all(),
        'like': item.like.all().count(),
        'collect': item.collect_set.all().count(),
        'minfund': item.minfund,
        'event': item.event,
    }
    return r_(0, data)

@api_view(['GET'])
def financeplan(req, pk):
    item = i(Project, pk)
    if not item: 
        return NOENTITY
    data = {
        'planfinance': item.planfinance,
        'share2give': item.share2give,
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
        return NOENTITY
    data = list()
    for item in project.member_set.all():
        data.insert(0, {
            'id': item.id,
            'photo': img(item.photo),
            'name': item.name,
            'position': item.position,
            'profile': item.profile,
        })
    return r_(0, data)


@api_view(['GET'])
def investlist(req, pk):
    queryset = Invest.objects.filter(project__pk=pk, valid=True)
    data = list()
    for item in queryset:
        user = item.user
        data.append({
            'amount': item.amount,
            'name': user.name,
            'photo': img(user.photo),
        })
    return r_(0, data)

@api_view(['GET'])
@login()
def attend(req, pk):
    project = i(Project, pk)
    if not project: 
        return NOENTITY
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
            'company': item.company,
            'position': item.position,
            'date': dateformat(item.create_datetime),
        }) 
    code = 2 if len(queryset) < size else 0
    return r_(code, data, '加载完毕')

def _institute(queryset, page):
    size = settings.DEFAULT_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        data.append({
            'id': item.id,
            'name': item.name,
            'legalperson': item.legalperson,
        }) 
    code = 2 if len(queryset) < size else 0
    return r_(code, data, '加载完毕')

@api_view(['GET'])
#@login()
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
#ps = Project.objects.annotate(invested_sum=Sum('investship__invest_amount')).filter(invested_sum__gte=F('planfinance'))

@api_view(['POST'])
@login()
def wantroadshow(req):
    uid = req.session.get('uid')
    if Roadshow.objects.filter(~Q(valid=True), user__pk=uid).exists(): return r(1, '您还有路演申请仍在审核中')
    user = User.objects.get(pk=uid)
    name = req.data.get('name', '').strip()
    company = req.data.get('company', '').strip()
    if not name or not company: return arg_('name or company')
    tel = req.data.get('tel', '').strip()
    if validtel(tel) == False: return r(1, '手机格式不正确')
    vcr = req.data.get('vcr')
    print(vcr)
    obj = Roadshow.objects.create(
        user=user, 
        comment=company, 
        contact_name=name, 
        contact_phone=tel,
        vcr = vcr,
    )
    return Response({'code':0, 'msg':'上传项目成功, 您的项目已成功入选项目库', 'data':obj.id})

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
        return r(1, '设置图像失败')
    return r(0, '设置图像成功')

@api_view(['POST'])
@login()
def bg(req):
   
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
    return r(0, '地址设置成功')

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
    queryset = Project.objects.filter(
        start__lte=now, 
        stop__gte=now,
    )
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
            'date': item.stop,
        }) 
    
    data = {
        'banner': banner,
        'announcement': {'title': '新三版在线', 'url': 'http://www.baidu.com'},
        'project': project,
        'platform': [
            {'key': '成功融资总额(元)', 'value': '56125895423'},
            {'key': '项目总数', 'value': '451231'},
            {'key': '投资人总人数', 'value': '254566'},
            {'key': '基金池总额(元)', 'value': '452122553144'},
        ],
    }
    return r_(0, data)    


@api_view(['POST'])
@login()
def credit(req):
    from phone.sanban18 import Credit
    wd = req.data.get('wd', '').strip()
    if not wd:
        return r(1, '关键词不能为空')

    data = Credit().outcome(wd)
    return r_(0, data)


@api_view(['GET', 'POST'])
@login()
def userinfo(req, uid=None):
    if req.method == 'GET':
        uid = uid if uid else s(req)
        user = i(User, uid)
        data = { 
            'uid': s(req),
            'tel': user.tel,
            'gender': user.gender,
            'photo': img(user.photo),
            'nickname': user.nickname,
            'name': user.name,
            'idno': user.idno,
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
        print(user.birthday)

        print(ret)
        return r(0, str(ret))

@api_view(['GET', 'POST'])
@login()
def auth(req):
    user = u(req)

    if req.method == 'GET':
        qualification = [{'key': i[0], 'value': i[1]} for i in QUALIFICATION]
        data = {'company': user.company, 'position': user.position, 'qualification': qualification}
        return r_(0, data)

    elif req.method == 'POST':
        if user.valid:
            return r(1, '认证已通过, 更改请联系客服')
        qualification = req.data.get('qualification', '').strip()
        qualification = set(qualification.split(','))
        choice = set(str(item[0]) for item in QUALIFICATION)
        idpic = req.data.get('file')

        if not qualification or not qualification <= choice:
            return r(1, '认证资格有误')
        
        comment = ''
        if 'institute' in req.data: # 机构认证
            institute = req.data.get('institute', '').strip()
            legalperson = req.data.get('legalperson', '').strip()
            
            if not institute or not CHINESE_RE.match(institute):
                return r(1, '机构输入有误')
            if not legalperson or not CHINESE_RE.match(institute):
                return r(1, '法人输入有误')

            comment = '%s %s' % (institute, legalperson)
        
        flag = store(user.idpic, idpic)
        if not flag:
            return r(1, '上传身份证失败')
        user.qualification = qualification
        user.comment = comment
        user.save()
        return r(0, '认证提交成功') 

@api_view(['GET'])
@login()
def like(req, pk, flag):
    user = u(req)
    project = i(Project, pk)
    if not project:
        return r(-2, '系统错误')
    if flag == '0':
        project.like.add(user)
        return r_(0, {'is_like': True})
    else:
        project.like.remove(user)
        return r_(0, {'is_like': False})

@api_view(['GET'])
@login()
def collect(req, pk, flag):
    user = u(req)
    project = i(Project, pk)
    if not project:
        return r(-2, '系统错误')
    if flag == '0':
        Collect.objects.create(user=user, project=project)
        return r_(0, {'is_collect': True})
    else:
        Collect.objects.filter(user=user, project=project).delete()
        return r_(0, {'is_collect': False})

@api_view(['GET'])
@login()
def collectfinancing(req, page):
    now = timezone.now()
    queryset = Collect.objects.filter(
        user=u(req),
        project__start__lte=now, 
        project__stop__gte=now,
    )
    return __collect(queryset, page)

@api_view(['GET'])
@login()
def collectfinanced(req, page):
    queryset = Collect.objects.filter(
        user=u(req),
        project__stop__lt=timezone.now()
    )
    return __collect(queryset, page)

def __collect(queryset, page):
    size = settings.DEFAULT_PAGESIZE
    queryset = q(queryset, page, size)
    data = list()
    for item in queryset:
        project = item.project
        data.append({
            'id': project.id,
            'img': img(project.img),
            'company': project.company.name,
            'start': dateformat(project.start),
            'stop': dateformat(project.stop),
        })
    code = 2 if len(queryset) < size else 0
    return r_(code, data, '加载完毕')

@api_view(['GET'])
@login()
def collectfinance(req, page):
    now = timezone.now()
    queryset = Collect.objects.filter( 
        Q(project__start__isnull=True) | 
        Q(project__start__gt=now),
        user=u(req)
    )
    return __collect(queryset, page)

@api_view(['POST', 'GET'])
@login()
def feedback(req):
    uid = req.session.get('uid')
    advice = req.data.get('advice', '').strip()
    MAIL('反馈', advice).send()
    return r(0, '反馈成功')

@api_view(['GET', 'POST'])
def keyword(req):
    industrys = Industry.objects.filter(~Q(valid=False))
    data = list()
    for keyword in industrys:
        tmp = dict()
        tmp['id'] = keyword.id
        tmp['word'] = keyword.name
        data.append(tmp)
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def projectsearch(req, pk, page):
    if pk == '0': 
        value = req.data.get('value').strip()
        if not value: return arg_('value')
        queryset = Project.objects.filter(company__name__contains=value)
    else: queryset = Project.objects.filter(company__industry__in=[int(pk),])
    return g_project(queryset, page)


@api_view(['GET', 'POST'])
@login()
def wantinvest(req, pk):
    flag = req.data.get('flag','').strip()
    if not re.match('^[01]$', flag): return ARG
    invest_amount = req.data.get('invest_amount', '').strip() # 投资金额
    if not PK_RE.match(invest_amount): return ARG
    investor = req.data.get('investor', '').strip() # 投资人id
    if not PK_RE.match(investor): 
        return  Response({'code':1, 'msg':'请选择您的投资人身份'})
    project = i_(Project, pk) # 项目
    if not project: return NOENTITY
    fund = project.leadfund if flag=='1' else project.followfund
    if int(invest_amount) < fund:
        return Response({'code':1, 'msg':'金额必须大于%s' % fund})
    uid = req.session.get('uid')
    investor_obj = Investor.objects.filter(pk=investor, user__pk=uid) # 投资人实体
    if not investor_obj.exists():
        return r(9, '该投资人不存在')
    investship = InvestShip.objects.filter(project__pk=pk, investor__pk=investor) #是否投资过
    if investship.exists():
        return r(1, '您已投资过该项目, 请到用户中心查看')
    InvestShip.objects.create(
        investor = investor_obj[0],
        project = project,
        invest_amount = invest_amount,
        lead = int(flag)
    )
    return r(0, '工信您, 投资信息提交成功')


@api_view(['GET', 'POST'])
@login()
def myroadshow(req):
    uid = req.session.get('uid')
    objs = Roadshow.objects.filter(user__pk=uid) 
    data = list()
    for obj in objs:
        tmp = dict()
        if obj.company:
            tmp['company'] = obj.company.name
        else:
            tmp['company'] = ''
        tmp['create_datetime'] = timeformat(obj.create_datetime)
        tmp['audit_datetime'] = timeformat(obj.create_datetime + timedelta(seconds=2))
        if obj.valid == None:
            tmp['handle_datetime'] = ''
        else:
            tmp['handle_datetime'] = timeformat(obj.handle_datetime)
        tmp['valid'] = obj.valid
        if obj.valid == True:
            tmp['reason'] = '申请成功' 
        elif obj.valid == False:
            tmp['reason'] = obj.reason 
        else:
            tmp['reason'] = '等待审核, 预计2天内处理完毕' 
        data.append(tmp)
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['GET', 'POST'])
@login()
def mycreateproject(req, page):
    uid = req.session.get('uid')
    ret = g_project( Project.objects.filter(roadshow__user__isnull=False, roadshow__user__pk=uid), page )
    return ret

@api_view(['GET', 'POST'])
@login()
def myinvestproject(req, page):
    uid = req.session.get('uid')
    ret = g_project( InvestShip.objects.filter(investor__user__pk=uid), page )
    return ret

@api_view(['POST'])
@login()
def token(req):

    key = req.data.get('key', '').strip()
    if not key: 
        return r(1, '上传视频名不能为空')

    user = u(req)
    if Roadshow.objects.filter(~Q(valid=True), user=user).exists():
        return r(1, '您还有路演申请仍在审核中')

    print(key)
    q = Auth(settings.AK, settings.SK)
    token = q.upload_token(settings.BN, key)
    token2 = q.upload_token(settings.BN, key, 7200, {'callbackUrl':'http://115.28.177.22:8000/phone/callback/', 
        'callbackBody':'name=$(fname)&hash=$(etag)'})
    print(token2)
    return Response({'code':0, 'msg':'', 'data':token2})

def createurl(name):
    if not name: return ''
    q = Auth(settings.AK, settings.SK)
    url = 'http://%s/%s' % (settings.BD, name)
    url = q.private_download_url(url, expires=3600)
    print(url)
    return url

@api_view(['POST', 'GET'])
def callback(req):
    name = req.data.get('name', '').strip()
    if not name: return arg_('name')
    url = createurl(name)
    return Response({'code':0, 'msg':'视频上传成功', 'data':url})

    
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
    project = i_(Project, pk)
    if not project: return NOENTITY
    uid = req.session.get('uid')
    if project.roadshow and  project.roadshow.user.id == uid: 
        return r(1, '你不可以给自己的项目投资哦')
    return r(0, '')

@api_view(['POST', 'GET'])
@login()
def isinvestor(req):
    uid = req.session.get('uid')
    investors = Investor.objects.filter(user__pk=uid)
    if not investors.exists():
        return r(9, '您还没有认证')
    elif investors.filter(valid=True).exists():
        return r(0, '您已经认证')
    elif investors.filter(valid=None).exists():
        return r(1, '您的认证尚在审核中')
    else:
        return r(1, '对不起, 您的认证失败')

@api_view(['POST'])
@login()
def valsession(req):
    return r(0)

@api_view(['POST', 'GET'])
def checkupdate(req, system):
    return r(1, '没有更新')
    queryset = Version.objects.filter(system__id=system)
    if not queryset: 
        return r(0, '')
    version = queryset[0] 
    data = dict()
    data['force'] = True #False
    data['edition'] = version.edition
    data['item'] = version.item
    data['href'] = version.href 
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def shareproject(req, pk):
    data = dict()
    data['title'] = '项目分享'
    data['img'] = '%s/static/app/img/icon.png' % settings.DOMAIN
    data['url'] = 'http://a.app.qq.com/o/simple.jsp?pkgname=com.jinzht.pro'
    data['content'] = '项目分享'
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def shareapp(req):
    data = dict()
    data['title'] = 'app分享'
    data['img'] = '%s/static/app/img/icon.png' % settings.DOMAIN
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

@api_view(['POST', 'GET'])
@login()
def topic(req, pk):
    content = req.data.get('content','')
    if content.strip() == '': return arg_('content') 
    project = i_(Project, pk)
    if not project: return NOENTITY
    at_topic = req.data.get('at_topic',0)
    if not at_topic: 
        at_topic = None
        msg = '发表话题成功'
    else: 
        at_topic = i_(Topic, at_topic)
        msg = '回复成功'
    uid = req.session.get('uid')
    user = User.objects.get(pk=uid) 
    if at_topic and at_topic.user == user:
        print(at_topic.user)
        print(user)
        return r(1, '不能给自己回复哦')
    topic = Topic.objects.create(
       project = project,
       user = user,
       at_topic = at_topic,
       content = content,
    )
    return Response({'code':0, 'msg':msg, 'data':topic.id})

def g_topiclist(queryset, page, at=True):
    queryset = q_(queryset, page)
    data = list()
    for item in queryset:
        tmp = dict()
        tmp['pid'] = item.project.id
        tmp['id'] = item.id
        tmp['img'] = img(item.user.img)
        if item.at_topic: 
            if at == True:
                tmp['name'] = '%s@%s' % (item.user.name, item.at_topic.user.name)
            else:
                tmp['name'] = '%s 回复了您' % (item.user.name)
        else: tmp['name'] = '%s' % (item.user.name)
        tmp['create_datetime'] = dt_(item.create_datetime) 
        tmp['content'] = item.content
        tmp['investor'] = Investor.objects.filter(user=item.user, valid=True).exists()
        data.append(tmp) 
    status = -int(len(queryset)<6)
    return Response({'code':status, 'msg':'加载完毕', 'data':data})

@api_view(['POST', 'GET'])
@login()
def topiclist(req, pk, page):
    queryset = Topic.objects.filter(project__pk=pk)
    ret = g_topiclist(queryset, page)
    return ret
   
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
    code = 2 if len(queryset) < size else 0
    return r_(code, data, '加载完毕')

@api_view(['GET'])
def news(req, pk, page):
    queryset = News.objects.filter(newstype__id=pk)
    return __news(queryset, page)

def sanban(request, name):
    return render(request, 'phone/sanban/%s' % name)

@api_view(['POST', 'GET'])
def sharenews(req, pk):
    news = i(News, pk) 
    if not news: 
        return r(-2)

    data = {
        'url': '%s/%s/%s' %(settings.DOMAIN, settings.NEWS_URL_PATH, news.name),
        'src': news.src,
        'title': news.title,
        'content': news.content,
    }
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['GET'])
def newsshare(req, pk):
    news = i(News, pk) 
    if not news: 
        return r(-2)
    news.share += 1
    news.save()
    return r(0)
        
@api_view(['POST', 'GET'])
def newsread(req, pk):
    news = i(News, pk) 
    if not news:
        return r(-2)
    news.read += 1
    news.save()
    return r(0)
    
@api_view(['POST', 'GET'])
def newssearch(req, pk, page):
    value = req.data.get('value', '').strip()
    if not value: return arg_('value')
    if pk == '0': queryset = News.objects.filter(title__contains=value)
    else: queryset = News.objects.filter(newstype__id=pk)
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
        return r(-2, '系统错误')
    inform.read = True
    inform.save()
    return r(0)

@api_view(['GET'])
@login()
def deleteinform(req, pk):
    inform = i(Inform, pk)
    if not inform:
        return r(-2, '系统错误')
    user = u(req)
    if inform.user == user:
        inform.delete()
        return r(0)
    return r(1, '不能删除他人评论')


@api_view(['GET'])
@login()
def hastopic(req):
    queryset = Topic.objects.filter(at__user=u(req), read=False)
    data = {'count':queryset.count()}
    return r_(0, data)

@api_view(['POST', 'GET'])
@login()
def topicread(req, page):
    uid = req.session.get('uid') 
    queryset = Topic.objects.filter(~Q(read=None), at_topic__user__id=uid) 
    ret = g_topiclist(queryset, page, False)
    return ret

@api_view(['POST', 'GET'])
@login()
def settopicread(req, pk):
    uid = req.session.get('uid')
    if pk == '0':
        queryset = Topic.objects.filter(at_topic__user__id=uid, read=False) 
        queryset.update(read=True)
        return r(0, '全部设为已读成功')
    topic = i_(Topic, pk)
    if not topic: return NOENTITY
    topic.read = None 
    topic.save()
    return r(0, '删除成功')

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
        'name': '%s' % (item.user.name),
        'uid': item.user.id,
        'photo': img(item.user.photo),
        'content': '%s' % (item.content),
    }
    if item.at:
        dct['at_uid'] = item.at.user.id
        dct['at_name'] = item.at.user.name
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
        'flag': item.user == user,
        'datetime': dt_(item.create_datetime),
        'name': item.user.name,
        'photo': img(item.user.photo),
        'content': item.content,
    } 
    news = item.news
    if news: 
        tmp['share'] = {
            'id': news.id,
            'title': news.title, 
            'img': img(news.img),
            'url': '%s/%s/%s' %(settings.DOMAIN, settings.NEWS_URL_PATH, news.name)
        }
    else:
        if not item.pic:
            tmp['pic'] = []
        else:
            tmp['pic'] = [ os.path.join(settings.DOMAIN, v) for v in item.pic.split(';') ]

    tmp['is_like'] = user in item.like.all()

    size = settings.FEELINGLIKE_PAGESIZE
    tmp['like'] = __feelinglike(item.like.all(), 0, size)
    tmp['remain_like'] = max(0, item.like.all().count() - size)

    queryset = FeelingComment.objects.filter(feeling=item, valid=None)
    size = settings.FEELINGCOMMENT_PAGESIZE
    tmp['comment'] = __feelingcomment(queryset, user, 0, size)
    tmp['remain_comment'] = max(0, queryset.count() - size)
    return tmp  

@api_view(['GET','POST'])
@login()
def getfeeling(req, pk):
    item = i_(Feeling, pk)
    if not item: return NOENTITY
    user = User.objects.get(pk = req.session.get('uid'))
    data = __feeling(item, user) 
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
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
    content = req.data.get('content', '').rstrip()
    relative_path = datetime.now().strftime('media/feeling/%Y/%m')
    absolute_path = os.path.join(settings.BASE_DIR, relative_path)   
    news = req.data.get('news', 0)
    news = i(News, news)

    if req.FILES: 
        mkdirp(absolute_path)
    elif not content and not news: 
        return r(1, '发表内容不能为空')

    relative_path_list = list()
    counter = 0 

    for k, v in req.FILES.items():
        ext = imghdr.what(v)
        if ext not in settings.ALLOW_IMG: 
            return r(1, '图片格式不正确')

        img_name = '{}.{}'.format(uuid.uuid4().hex, ext)
        img = os.path.join(absolute_path, img_name)

        with open(img, 'wb') as fp:
            for data in v.chunks(): 
                fp.write(data)
        relative_path_list.append( os.path.join(relative_path, img_name) )
        counter += 1
        if counter == 9:
            break


    user = u(req) 
    obj = Feeling.objects.create(
        user = user,
        content = content,
        pic = ';'.join(relative_path_list),
        news = news
    )
    data = __feeling(obj, user) 
    return r_(0, data, '发表成功')

@api_view(['POST'])
@login()
def deletefeeling(req, pk):
    item = i(Feeling, pk)
    if not item: 
        return r(-2, '系统错误')
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
        return r(-2, '系统错误')
    user = u(req) 
    data = { 
        'is_like': not int(is_like),
        'name': user.name,
        'uid': user.id,
        'photo': img(user.photo),
    }
    if is_like == '0': 
        item.like.add(user)
        return r_(0, data, '点赞成功')
    else: 
        item.like.remove(user)
        return r_(0, data, '取消点赞')

@api_view(['GET'])
@login()
def feelinglikers(req, pk, page):
    item = i(Feeling, pk)
    if not item:
        return r(-2, '系统错误')
    queryset = item.like.all()
    size = settings.FEELINGLIKE_PAGESIZE
    data = __feelinglike(queryset, page, size)
    code = 2 if len(data) < size else 0
    return r_(code, data)

@api_view(['GET'])
@login()
def feelingcomment(req, pk, page):
    item = i(Feeling, pk)
    if not item: return NOENTITY
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
        return r(-2, '系统错误')
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

@api_view(['POST'])
@login()
def hidefeelingcomment(req, pk):
    item = i(FeelingComment, pk)
    if not item: 
        return r(-2, '系统错误')
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
    return r(0, 'test')
