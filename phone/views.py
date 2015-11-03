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
from PIL import Image as Img
#import StringIO

PK_RE = re.compile(r'^[1-9]\d*$')
MTM_RE = re.compile(r'^[1-9]\d*(,[1-9]\d*)*$')
NOENTITY = Response({'code':1, 'msg':'操作异常'})
DEBUG = True

def r(code, msg=''):
    return Response({'code': code, 'msg': msg}) 

def r_(code, data, msg=''):
    return Response({'code': code, 'msg': msg, 'data': data})

def q(QuerySet, page, size=4):
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

def valimg(img):
    return imghdr.what(img) in ('jpeg', 'png') 

def store(file_field, image, upload_to=''):
     
    #img = Img.open(StringIO.StringIO(self.image.read()))
    #if img.mode != 'RGB':
    #    img = img.convert('RGB')
    #img.thumbnail((image.width/1.5, image.height/1.5), Img.ANTIALIAS)
    #output = StringIO.StringIO()
    #img.save(output, format='JPEG', quality=70)
    #output.seek(0)
    #image= InMemoryUploadedFile(output,'ImageField', "%s.jpg" %self.image.name.split('.')[0], 'image/jpeg', output.len, None)
    name = image.name
    pth = datetime.now().strftime(upload_to)
    file_field.save('%s/%s' % (pth, name), File(image)) 

def arg_(field='参数'):
    return Response({'status': ERR, 'msg': '%s' % field})

def img(file, default=''):
    if not file: return '%s/media/default/coremember.png' % settings.RES_URL
    return '%s%s' % (settings.RES_URL, file.url)

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
            if regid: # 如果redid存在
                user.regid = regid
                user.version=version
                user.save()
            return r(0, '登录成功')
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


@api_view(['GET', 'POST'])
def banner(rquest):
    queryset= Banner.objects.reverse()[:4]
    data = list()
    for item in queryset:
        data.append({
            'img': img(item.img),
            'project': item.project.id if item.project else None,
            'url': item.url
        })
    return Response({'code':0, 'msg': '', 'data':data})


def project_stage(project):
    now = timezone.now()
    if not project.roadshow_start_datetime:
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
    elif now < project.roadshow_start_datetime: # 现在时间 < 路演开始时间
        stage = { 
                    'flag': 1,
                    'code': '路演预告', 
                    'color': 0xE69781,
                    'start': {
                        'name':'路演时间', 
                        'datetime':dateformat(project.roadshow_start_datetime)
                        },
                    'end': {
                        'name':'报名截止', 
                        'datetime': dateformat(project.roadshow_start_datetime - timedelta(days=2))
                        }
                }

    elif now > project.roadshow_stop_datetime:
        if now > project.finance_stop_datetime:
            stage = {
                    'flag': 3,
                    'code': '融资完毕', 
                    'color': 0xDC471C,
                    'start': {
                        'name': '众筹时间', 
                        'datetime': dateformat(project.roadshow_start_datetime),
                    },
                    'end': {
                        'name': '截止时间', 
                        'datetime': dateformat(project.finance_stop_datetime)
                    }
                }
        else:
            stage = {
                    'flag': 2,
                    'code': '融资进行', 
                    'color': 0xD4A225,
                    'start': {
                        'name': '众筹时间', 
                        'datetime': dateformat(project.roadshow_start_datetime),
                    },
                    'end': {
                        'name': '截止时间', 
                        'datetime': dateformat(project.finance_stop_datetime)
                    }
                }
    else:
            stage = {
                    'flag': 2,
                    'code': '融资进行', 
                    'color': 0xD4A225,
                    'start': {
                        'name': '众筹时间', 
                        'datetime': dateformat(project.roadshow_start_datetime),
                    },
                    'end': {
                        'name': '截止时间', 
                        'datetime': dateformat(project.finance_stop_datetime)
                    }
                }
    return stage

@api_view(['POST', 'GET'])
def project(req, page=0):
    ret = g_project( Project.objects.all(), page) 
    return ret

@api_view(['POST', 'GET'])
def thinktankdetail(req, pk):
    item = i_(Thinktank, pk)
    if not item: return NOENTITY
    data = dict()
    data['url'] = item.video
    data['experience'] = item.experience
    data['success_cases'] = item.success_cases
    data['good_at_field'] = item.good_at_field
    return Response({'code':0, 'msg':'', 'data':data})
    
@api_view(['POST', 'GET'])    
def thinktank(req, page):
    queryset = q_(Thinktank.objects.all(), page)
    data = list()
    for item in queryset:
        tmp = dict()
        tmp['id'] = item.id
        tmp['img'] = '%s%s' %(RES_URL, item.img.url)
        tmp['thumbnail'] = '%s%s' %(RES_URL, item.img.url)
        tmp['name'] = item.name
        tmp['company'] = item.company
        tmp['title'] = item.title
        tmp['experience'] = item.experience
        data.append(tmp)
    status = -int(len(queryset)<PAGE_SIZE)
    return Response({'code':status, 'msg':'加载完毕', 'data':data})

def videourl(name):
    q = Auth(settings.AK, settings.SK)
    base_url = 'http://%s/%s' % (settings.BD, name)
    private_url = q.private_download_url(base_url, expires=3600)
    return private_url

def investamountsum(flag, project):
    if flag == 1: return 0
    elif flag == 2:
        tmp = InvestShip.objects.filter(project=project, valid=True).aggregate(Sum('invest_amount'))['invest_amount__sum']
        if not tmp: tmp = 0 
        return (tmp + int(project.finance2get))
    else: return project.finance2get

@api_view(['POST', 'GET'])
#@login()
def projectdetail(req, pk):
    project = i_(Project, pk)
    if not project: return NOENTITY
    data = dict()
    data['company_name'] = project.company.name
    data['stage'] = project_stage(project)
    data['participator2plan'] = project.participator2plan
    data['plan_finance'] = project.planfinance
    data['project_img'] = '%s%s' %(RES_URL, project.img.url)
    data['project_video'] = project.url or createurl(project.roadshow.vcr if project.roadshow else '')
    data['invest_amount_sum'] = investamountsum(data['stage']['flag'], project)
    uid = req.session.get('uid')
    data['is_participator'] = ParticipateShip.objects.filter(project__pk=pk, user__pk=uid).exists()
    ret = lcv(project)
    data['like_sum'] = ret['like_sum']
    data['collect_sum'] = ret['collect_sum']
    data['vote_sum'] = ret['vote_sum']
    data['company_profile'] = '    ' + project.company.profile
    data['business'] = '    ' + project.business
    data['project_desc'] = '    ' + project.desc
    data['business_model'] = '    ' + project.model
    data['leadfund'] = project.leadfund
    data['followfund'] = project.followfund
    pes = project.projectevent_set.all()
    if pes.exists():
        e = pes[0]
        data['project_event'] = {
            'event_date':dateformat(e.happen_datetime),
            'event_detail':'    ' + e.detail,
            'event_title':e.title
        }
    else:
        data['project_event'] = None
    return Response({'code': 0, 'msg': '', 'data': data})

@api_view(['POST', 'GET'])
def financeplan(req, pk):
    item = i_(Project, pk)
    if not item: return NOENTITY
    data = dict()
    data['plan_finance'] = item.planfinance
    data['finance_pattern'] = item.pattern
    data['share2give'] = item.share2give
    data['fund_purpose'] = item.usage
    data['quit_way'] = item.quitway
    return Response({'code':0, 'msg':'', 'data': data})

@api_view(['POST', 'GET'])
def coremember(req, pk):
    project = i_(Project, pk)
    if not project: return NOENTITY
    data = list()
    queryset = project.coremember_set.all()
    for item in queryset:
        tmp = dict()
        tmp['id'] = item.id
        tmp['img'] = img(item.img)
        tmp['name'] = item.name
        tmp['title'] = item.title
        tmp['profile'] = item.profile
        data.insert(0, tmp)
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def corememberdetail(req, pk):
    coremember = i_(CoreMember, pk)
    if not coremember: return NOENTITY
    data = dict()
    data['profile'] = coremember.profile
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def projectinvestorlist(req, pk):
    queryset = InvestShip.objects.filter(project__pk=pk, valid=True)
    data = list()
    for item in queryset:
        tmp = dict()
        investor = item.investor
        user = investor.user
        tmp['certificate_datetime'] = dateformat(investor.certificate_datetime)
        tmp['invest_amount'] = item.invest_amount
        tmp['real_name'] = user.name
        tmp['user_img'] = img(user.img)
        data.append(tmp)
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def projectevent(req, pk):
    queryset = ProjectEvent.objects.filter(project__pk=pk)
    data = list()
    for item in queryset:
        tmp = dict()
        tmp['event_title'] = item.title
        tmp['event_detail'] = item.detail
        tmp['event_date'] = item.happen_datetime
        data.append(tmp)
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
@login()
def participate(req, pk):
    project = i_(Project, pk)
    if not project: return NOENTITY
    user = User.objects.get(pk=req.session.get('uid'))
    item = ParticipateShip.objects.filter(project=project, user=user)
    if item.exists(): return r(1, '您已申请参加该项目路演, 无需重复报名')
    ParticipateShip.objects.create(project=project, user=user)
    return r(0, '恭喜您, 申请成功')

@api_view(['GET'])
def defaultclassify(req): return Response({'code':0, 'msg':'', 'data':0})

def g_project(queryset, page): 
    queryset = q_(queryset, page)
    if not queryset: return Response({'code':-1, 'msg':'加载完毕', 'data':[]})
    if isinstance(queryset[0], Project): flag = 'p'
    elif isinstance(queryset[0], RecommendProject): flag = 'r'
    elif isinstance(queryset[0], InvestShip): flag = 'i'
    elif isinstance(queryset[0], CollectShip): flag= 'c'
    data = list()
    for i, project in enumerate(queryset):
        tmp = dict()
        if flag == 'r': tmp['reason'] = project.reason
        if flag != 'p': project = project.project
        tmp['id'] = project.id
        tmp['thumbnail'] = '%s%s' %(RES_URL, project.thumbnail.url)
        tmp['project_summary'] = project.summary
        company_name = re.sub(r'(股份)?有限(责任)?公司', '', project.company.name)
        tmp['company_name'] = company_name
        tmp['province'] = project.company.province
        tmp['city'] = project.company.city
        tmp['industry_type'] = [it.name for it in project.company.industry.all()]
        ret = lcv(project)
        tmp['like_sum'] = ret['like_sum']
        tmp['collect_sum'] = ret['collect_sum']
        tmp['vote_sum'] = ret['vote_sum']
        stage = project_stage(project)
        tmp['stage'] = stage
        if stage['flag'] == 3: tmp['invest_amount_sum'] = project.finance2get # 融资完成的显示
        data.append(tmp)
    status = -int(len(queryset)<PAGE_SIZE)
    return Response({'code':status, 'msg':'加载完毕', 'data':data})

@api_view(['POST', 'GET'])
def recommendproject(req, page):
    ret = g_project( RecommendProject.objects.all(), page )
    return ret

@api_view(['POST', 'GET'])
def waitforfinance(req, page):
    #ps = Project.objects.filter(roadshow_start_datetime__lt=timezone.now().date()).annotate(invested_sum=Sum('investship__invest_amount')).filter(Q(invested_sum__isnull=True) | Q(invested_sum=0) ) 
    now = timezone.now()
    ret = g_project( Project.objects.filter(roadshow_start_datetime__lte=now, finance_stop_datetime__gte=now), page )
    return ret

@api_view(['POST', 'GET'])
def finishfinance(req, page):
    #ps = Project.objects.annotate(invested_sum=Sum('investship__invest_amount')).filter(invested_sum__gte=F('planfinance'))
    now = timezone.now()
    ret = g_project( Project.objects.filter(finance_stop_datetime__lt = now), page )
    return ret

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

@api_view(['POST', 'GET'])
@login()
def activity(req):
    if not Activity.objects.all().exists(): return r(1, '目前没有活动')
    ac = Activity.objects.all()[0]
    if timezone.now() > ac.stop_datetime: return r(1, '目前没有活动')
    data = dict()
    data['id'] = ac.id
    data['summary'] = ac.summary
    utc = pytz.UTC
    seconds = (ac.start_datetime - utc.localize(datetime.now())).total_seconds()
    data['seconds'] = seconds
    data['start_datetime'] = dateformat(ac.start_datetime)
    data['longitude'] = ac.longitude
    data['latitude'] = ac.latitude
    data['coordinate'] = ac.coordinate
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
@login()
def signin(req, pk):
    item = i_(Activity, pk)
    if not item: return NOENTITY
    user = User.objects.get(pk=req.session.get('uid'))
    if Signin.objects.filter(user=user, activity=item).exists(): return r(0, '你已签到, 无需重复签到')
    if timezone.now() > item.stop_datetime: return r(1, '对不起, 此活动已结束')
    Signin.objects.create(user=user, activity=item)
    return r(0, '恭喜您, 签到成功!')

#@api_view(['POST'])
#@login()
#def addcompany(req):
#    uid = req.session.get('uid')
#    user = User.objects.get(pk=uid)
#    invalids = JoinShip.objects.filter(~Q(valid=True), user=user)
#    if invalids.exists(): return r(1, '您尚有公司在审核中, 请耐心等待')
#    name = req.data.get('company_name')
#    company = Company.objects.filter(name=name)
#    if company.exists(): company = company[0]
#    else:
#        province = req.data.get('province')
#        city = req.data.get('city')
#        industry= req.data.get('industry_type').split(',')
#        companystatus = req.data.get('company_status')
#        company = Company.objects.create(
#            name = name,
#            province = province,
#            city = city,
#            companystatus = Companystatus.objects.get(pk=companystatus)
#        )
#        company.industry= industry
#
#    if not JoinShip.objects.filter(user__pk=uid, company__pk=company.id).exists():
#        JoinShip.objects.create(user=user,company=company)
#    data = dict()
#    data['id'] = company.id
#    data['company'] = company.name
#    return Response({'code':0, 'msg':'公司添加成功', 'data':data})

@api_view(['POST'])
@login()
def editcompany(req, pk):
    return r(0, '')

#@api_view(['POST', 'GET'])
#def companyinfo(req, pk):
#    item = i_(Company, pk)
#    if not item: return NOENTITY
#    data = dict()
#    data['industry_type'] = [it.name for it in item.industry.all()]
#    data['province'] = item.province
#    data['city'] = item.city
#    data['company_status'] = item.companystatus.name
#    return Response({'code':0, 'msg':'', 'data':data})

#@api_view(['POST', 'GET'])
#@login()
#def companylist(req):
#    user = User.objects.get(pk=req.session.get('uid'))
#    data = [{'id':o.id, 'company_name':o.name} for o in user.company.all()]
#    return Response({'code':0, 'msg':'', 'data':data})

#@api_view(['POST', 'GET'])
#def industry(req):
#    data = [{'id':o.id, 'type_name':o.name} for o in Industry.objects.all()]
#    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def companystatus(req):
    data = [{'id':o.id, 'status_name':o.name} for o in Companystatus.objects.all()]
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def investorqualification(req):
    data = [{'id':o.id, 'desc':o.desc} for o in Qualification.objects.all()]
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def fundsizerange(req):
    data = [{'id':o.id, 'desc':o.desc} for o in FundSizeRange.objects.all()]
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
@login()
def authenticate(req):
    name = req.data.get('name','').strip()
    position = req.data.get('position', '').strip()
    company = req.data.get('company','').strip()
    if not name or not position or not company: return arg_('请完善信息')
    qualification = req.data.get('qualification','').strip()
    if not MTM_RE.match(qualification): return arg_('qualification')

    user = User.objects.get(pk=req.session.get('uid'))
    queryset = Investor.objects.filter(user=user)

    if queryset.exists():
        valid = queryset[0].valid
        if valid == None: return r(1, '该身份认证正在审核中')
        elif valid == False: return r(1, '认证失败, 请去用户中心查看详情')
        else: return r(1, '认证成功')
    
    investor = Investor.objects.create(
         user=user,
         position = position,
         comment = company
    )
    investor.qualification = qualification.split(',')
    user.name = name; user.save()
    return r(0, '提交成功, 等待审核')

@api_view(['POST', 'GET'])
@login()
def businesscard(req, pk):
    investor = Investor.objects.get(pk=pk)
    store_(
        investor.card,
        req.data.get('file'),
        'investor/%Y/%m'
    )
    return r(0, '名片上传成功')


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
    if not valimg(photo):
        return r(1, '图片格式不正确')

    user = u(req)
    store(user.photo, photo)
    data = {'photo': img(user.photo)}
    return r_(0, data, '设置图像成功')

@api_view(['POST'])
@login()
def bg(req):
   
    bg = req.data.get('file')
    if not bg:
        return r(1, '图像不能为空')    
    if not valimg(photo):
        return r(1, '图片格式不正确')

    user = u(req)
    store(user.bg, bg)
    data = {'bg': img(user.bg)}
    return r_(0, data, '设置背景成功')

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
def annc(req):
    data = {
        'title': '新三板资讯',
        'url': 'http://www.baidu.com',
    }
    return r_(0, data)


@api_view(['GET'])
@login()
def credit(req):
    data = {
        'title': '新三板资讯',
        'url': 'http://www.baidu.com',
    }
    return r_(0, data)

@api_view(['GET'])
@login()
def platform(req):
    data = [
        {'key': '成功融资总额(元)', 'value': '56125895423'},
        {'key': '项目总数', 'value': '451231'},
        {'key': '投资人总人数', 'value': '254566'},
        {'key': '基金池总额(元)', 'value': '452122553144'},
    ]
    return r_(0, data)


@api_view(['POST', 'GET'])
@login()
def userinfo(req):

    u = u(req) 

    if req.method == 'GET':
        data = { 'uid': s(req),
            'photo': img(u.photo),
            'nickname': u.nickname,
            'name': u.name,
            'idno': u.idno,
            'company': u.company,
            'position': u.position,
            'email': u.email,
            'addr': u.addr}
        return r_(0, data)

    elif req.method == 'POST':
        name = req.data.get('name', '').strip() 
        idno = req.data.get('idno', '').strip()
        email = req.data.get('email', '').strip()
        company = req.data.get('company', '').strip()
        position = req.data.get('position', '').strip()
        addr = req.data.get('position', '').strip()

@api_view(['POST'])
@login()
def like(req, pk):
    uid = req.session.get('uid')
    action = req.data.get('action') 
    if action == '1':
        LikeShip.objects.create(
            user = User.objects.get(pk=uid),
            project = Project.objects.get(pk=pk)
        )
        return r(0, '点赞成功')
    else:
        LikeShip.objects.filter(
            user__pk=uid,
            project__pk=pk
        ).delete()
        return r(0, '取消点赞')

@api_view(['POST'])
@login()
def collect(req, pk):
    uid = req.session.get('uid')
    action = req.data.get('action') 
    if action == '1':
        CollectShip.objects.create(
            user = User.objects.get(pk=uid),
            project = Project.objects.get(pk=pk)
        )
        return r(0, '收藏成功')
    else:
        CollectShip.objects.filter(
            user__pk=uid,
            project__pk=pk
        ).delete()
        return r(0, '取消收藏')

@api_view(['POST'])
@login()
def modifyposition(req):
    position = req.data.get('position_type', '').strip()
    if not MTM_RE.match(position): return arg_('position')
    user = User.objects.get(pk=req.session.get('uid'))
    user.position = position.split(',')
    return r(0, '职位设置成功')

def lcv(project, uid=0): # like collect vote
    data = dict()
    ls = LikeShip.objects.filter(project=project)
    data['like_sum'] = ls.count()# + random.randint(100, 200) 
    cs = CollectShip.objects.filter(project=project)
    data['collect_sum'] = cs.count()# + random.randint(100, 200) 
    vs = VoteShip.objects.filter(project=project)
    data['vote_sum'] = vs.count()# + random.randint(100, 200)
    return data

@api_view(['GET', 'POST'])
@login()
def collectfinancing(req, page):
    uid = req.session.get('uid')
    now = timezone.now()
    queryset = CollectShip.objects.filter(
        user__pk=uid, 
        project__roadshow_start_datetime__lte=now, 
        project__finance_stop_datetime__gte=now,
    )
    return  g_project(queryset, page)

@api_view(['GET', 'POST'])
@login()
def collectfinanced(req, page):
    uid = req.session.get('uid')
    now = timezone.now()
    queryset = CollectShip.objects.filter(
        user__pk=uid,
        project__finance_stop_datetime__lt=now
    )
    return g_project(queryset, page)

@api_view(['GET', 'POST'])
@login()
def collectroadshow(req, page=0):
    uid = req.session.get('uid')
    now = timezone.now()
    queryset = CollectShip.objects.filter(
        Q(project__roadshow_start_datetime__isnull=True) | 
        Q(project__roadshow_start_datetime__gt=now),
        user__pk=uid, 
    )
    return g_project(queryset, page)

@api_view(['POST', 'GET'])
@login()
def feedback(req):
    uid = req.session.get('uid')
    advice = req.data.get('advice', '').strip()
    if not advice: return ARG
    #if Feedback.objects.filter(user__pk=uid, valid=None).exists():
    #    return r(0, '')
    Feedback.objects.create(
        user = User.objects.get(pk=uid),
        advice = advice
    )
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
def generalinformation(req, pk=None):
    if pk: uid = pk
    else: uid = req.session.get('uid')
    data = dict()
    data['uid'] = uid
    data['tel'] = User.objects.get(pk=uid).tel
    user = User.objects.get(pk=uid)
    data['user_img'] = img(user.img)
    data['real_name'] = user.name
    data['gender'] = user.gender
    data['position_type'] = [pt.name for pt in user.position.all()]
    data['province'] = user.province
    data['city'] = user.city
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
@login()
def myinvestorlist(req):
    uid = req.session.get('uid')
    ivs = Investor.objects.filter(user__pk=uid, valid=True)
    data = list()
    for iv in ivs:
        tmp = dict()
        tmp['id'] = iv.id
        if iv.company is None:
            tmp['company'] = '自然人'
        else:
            tmp['company'] = iv.company.name
        data.append(tmp)
    return Response({'code':0, 'msg':'', 'data':data})
        
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
def myinvestorauthentication(req):
    uid = req.session.get('uid')
    invs = Investor.objects.filter(user__pk=uid) 
    data = list()
    for inv in invs:
        tmp = dict()
        tmp['id'] = inv.id
        tmp['company'] = inv.company.name if inv.company else '自然人'
        tmp['apply_for_certificate_datetime'] = timeformat(inv.create_datetime)
        tmp['audit_date'] = timeformat(inv.create_datetime + timedelta(seconds=2))
        tmp['certificate_datetime'] = timeformat(inv.certificate_datetime)
        tmp['is_qualified'] = inv.valid
        if inv.valid == True:
            tmp['reject_reason'] = '认证成功' 
        elif inv.valid == False:
            tmp['reject_reason'] = inv.reason 
        else:
            tmp['reject_reason'] = '等待审核, 预计2天内处理完毕'
        data.append(tmp)
    return Response({'code':0, 'msg':'', 'data':data})

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
def myparticipate(req):
    uid = req.session.get('uid')
    objs = ParticipateShip.objects.filter(user__pk=uid) 
    data = list()
    for obj in objs:
        tmp = dict()
        tmp['id'] = obj.project.id
        tmp['company'] = obj.project.company.name
        tmp['project'] = obj.project.summary
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

@api_view(['POST', 'GET'])
@login()
def investorinfo(req, pk):
    investor = i_(Investor, pk)
    if not investor: return NOENTITY
    data = dict()
    data['investor_type'] = 1 if investor.company else 0 
    if investor.company: #机构投资人
        data['company'] = investor.company.name
        data['industry'] = [it.name for it in investor.industry.all()]
        data['fund_size_range'] = investor.fundsizerange.desc
    else: #自然投资人
        user = investor.user
        data['real_name'] = user.name
        data['tel'] = investor.user.tel
        data['province'] = user.province
        data['city'] = user.city
        data['company'] = investor.comment
        data['position'] = investor.position
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST'])
@login()
def issessionvalid(req):
    return r(0, 'session合法')

@api_view(['POST', 'GET'])
def contactus(req):
    data = {'tel':'18681838312', 'name':'徐力'}
    return Response({'code':0, 'msg':'', 'data':data})

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
    data['img'] = '%s/static/app/img/icon.png' % settings.RES_URL
    data['url'] = 'http://a.app.qq.com/o/simple.jsp?pkgname=com.jinzht.pro'
    data['content'] = '项目分享'
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def shareapp(req):
    data = dict()
    data['title'] = 'app分享'
    data['img'] = '%s/static/app/img/icon.png' % settings.RES_URL
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

@api_view(['POST', 'GET'])
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
    size = 6
    queryset = q_(queryset, page, size)
    data = list()
    for item in queryset:
        tmp = dict()
        tmp['id'] = item.id
        tmp['title'] = item.title
        tmp['source'] = item.source
        tmp['content'] = item.content
        tmp['img'] = item.img
        tmp['create_datetime'] = dt_(item.create_datetime) 
        tmp['readcount'] = item.readcount
        tmp['sharecount'] = item.sharecount
        tmp['href'] = '%s/%s/%s/' %(settings.RES_URL, 'phone/xinwei', item.name)
        data.append(tmp)
    code = -int(len(queryset)<size)
    return Response({'code': code, 'msg':'加载完毕', 'data':data})

@api_view(['GET'])
def news(req, pk, page):
    queryset = News.objects.filter(newstype__id=pk)
    return __news(queryset, page)

def xinwei(request, name):
    return render(request, 'phone/xinwei/%s' % name)

@api_view(['POST', 'GET'])
def sharenews(req, pk):
    news = i_(News, pk) 
    if not news: return NOENTITY 
    data = dict()
    data['href'] = '%s/%s/%s' %(settings.RES_URL, settings.NEWS_URL_PATH, news.name)
    data['src'] = news.src 
    data['title'] = news.title
    data['content'] = news.content
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def newssharecount(req, pk):
    news = i_(News, pk) 
    if not news: return NOENTITY 
    news.sharecount += 1
    news.save()
    return r(0, '')
        
@api_view(['POST', 'GET'])
def newsreadcount(req, pk):
    news = i_(News, pk) 
    if not news: return NOENTITY 
    news.readcount += 1
    news.save()
    return r(0, '')
    
@api_view(['POST', 'GET'])
def newssearch(req, pk, page):
    value = req.data.get('value', '').strip()
    if not value: return arg_('value')
    if pk == '0': queryset = News.objects.filter(title__contains=value)
    else: queryset = News.objects.filter(newstype__id=pk)
    return __news(queryset, page)

@api_view(['POST', 'GET'])
def newstype(req):
    data = [{'key':item.id, 'value':item.name} for item in NewsType.objects.filter(~Q(valid=False))]
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def knowledgetag(req):
    data = []
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
@login()
def hasinform(req):
    uid = req.session.get('uid')
    queryset = Inform.objects.filter(user__pk=uid, read=False)
    data = {'count': queryset.count()}
    return Response({'code':0, 'msg':'', 'data':data})    

@api_view(['POST', 'GET'])
@login()
def systeminform(req, page):
    uid = req.session.get('uid')
    queryset = SystemInform.objects.filter(user__pk=uid)
    queryset = q_(queryset, page)
    data = list()
    for item in queryset:
        extras = {'api': item.push.msgtype.name,
            '_id': item.push._id,
            'url': item.push.url
        }
        tmp = dict()
        tmp['id'] = item.id
        tmp['title'] = item.push.msgtype.desc
        tmp['content'] = item.push.content
        tmp['extras'] = extras
        tmp['create_datetime'] = timeformat(item.create_datetime)
        tmp['read'] = item.read
        data.append(tmp)
    return Response({'code':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
@login()
def setsysteminform(req, pk):
    systeminform = i_(SystemInform, pk)
    if not systeminform: return arg_('systeminform')
    systeminform.read = True
    systeminform.save()
    return Response({'code':0, 'msg':'', 'data':systeminform.read})

@api_view(['POST', 'GET'])
@login()
def deletesysteminform(req, pk):
    systeminform = i_(SystemInform, pk)
    if not systeminform: return arg_('systeminform')
    uid = req.session.get('uid')
    user = User.objects.get(pk=uid)
    if systeminform.user == user:
        systeminform.delete()
        return r(0, '删除成功')
    return r(1, '不能删除别人的消息')

@api_view(['GET'])
@login()
def hastopic(req):
    user = User.objects.get(pk=s(req)) 
    queryset = Topic.objects.filter(at__user=user, read=False)
    return Response({'code':0, 'msg':'', 'data':{'count':queryset.count()}})

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

def g_feelinglikers(queryset, page, pagesize=settings.FEELINGLIKERS_INITAL_PAGESIZE): 
    queryset = q_(queryset, page, pagesize)
    data = list()
    for item in queryset:
        tmp = dict()
        tmp['name'] = item.name
        tmp['uid'] = item.id
        tmp['photo'] = img(item.img)
        data.append(tmp)
    return data

def __feelingcomment(item, user):
    tmp = dict()
    tmp['id'] = item.id
    tmp['flag'] = item.user == user
    tmp['name'] = '%s' % (item.user.name)
    tmp['uid'] = item.user.id
    tmp['photo'] = img(item.user.img)
    if item.at:
        tmp['at_label'] = settings.AT_LABEL
        tmp['at_uid'] = item.at.user.id
        tmp['at_name'] = item.at.user.name
    tmp['label_suffix'] = settings.LABEL_SUFFIX
    tmp['content'] = '%s' % (item.content)
    return tmp

def g_feelingcomment(queryset, user, page):
    queryset = q_(queryset, page, settings.FEELINGCOMMENT_PAGESIZE)
    data = list()
    for item in queryset:
        tmp = __feelingcomment(item, user)
        data.append(tmp)
    return data
       
def __feeling(item, user): # 获取发表的状态的关联信息
    tmp = dict()
    tmp['id'] = item.id
    tmp['uid'] = item.user.id
    tmp['flag'] = item.user == user
    tmp['datetime'] = dt_(item.create_datetime)
    tmp['name'] = item.user.name
    tmp['photo'] = img(item.user.img)
    tmp['content'] = item.content
    news = item.news
    if news: 
        tmp['share'] = {
            'id': news.id,
            'title': news.title, 
            'src': news.src,
            'href': '%s/%s/%s' %(settings.RES_URL, settings.NEWS_URL_PATH, news.name)
        }
    else:
        tmp['pics'] = [] if item.pics==''  else [ os.path.join(settings.RES_URL, v) for v in item.pics.split(';') ]
    tmp['is_like'] = user in item.likers.all()
    tmp['likers'] = g_feelinglikers(item.likers.all(), 0) # page_size=3
    remain_likers_num = item.likers.all().count() - settings.FEELINGLIKERS_INITAL_PAGESIZE
    tmp['remain_likers_num'] = 0 if remain_likers_num <=0 else remain_likers_num
    tmp['position'] = [ v.name for v in item.user.position.all() ]
    tmp['city'] = item.user.city 
    queryset = Feelingcomment.objects.filter(feeling=item, valid=None)
    data = g_feelingcomment(queryset, user, 0)
    tmp['comment'] = data
    remain_comment_num = queryset.count() - 15
    tmp['remain_comment_num'] = 0 if remain_comment_num <=0 else remain_comment_num 
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
    user = User.objects.get(pk=req.session.get('uid'))
    pagesize = settings.FEELING_PAGESIZE
    queryset = q_(Feeling.objects.all(), page, pagesize) 
    data = list()
    for item in queryset: data.append( __feeling(item, user) )
    status = -(len(data) < pagesize)
    return Response({'code':status, 'msg':'', 'data':data})

@api_view(['POST'])
@login()
def postfeeling(req):
    content = req.data.get('content', '').rstrip()
    relative_path = datetime.now().strftime('media/feeling/%Y/%m')
    absolute_path = os.path.join(settings.BASE_DIR, relative_path)   
    news = req.data.get('news', 0)
    news = i_(News, news)
    if req.FILES: mkdirp(absolute_path)
    elif not content and not news: return r(1, '发表内容不能为空')
    relative_path_list = list()
    for k, v in req.FILES.items():
        ext = imghdr.what(v)
        if ext not in settings.ALLOW_IMG: return r(1, '图片格式不正确')
        img_name = '{}.{}'.format(uuid.uuid4().hex, ext)
        img = os.path.join(absolute_path, img_name)
        with open(img, 'wb') as fp:
            for data in v.chunks(): fp.write(data)
        relative_path_list.append( os.path.join(relative_path, img_name) )
    uid = req.session.get('uid')
    user = User.objects.get(pk=uid)
    obj = Feeling.objects.create(
        user = user,
        content = content,
        pics = ';'.join(relative_path_list),
        news = news
    )
    data = __feeling(obj, user) 
    return Response({'code':0, 'msg':'发表成功', 'data':data})

@api_view(['POST'])
@login()
def deletefeeling(req, pk):
    item = i_(Feeling, pk)
    if not item: return NOENTITY
    user = User.objects.get(pk=req.session.get('uid'))
    if item.user == user:
        item.delete()
        return r(0, '删除状态成功')
    return r(1, '不能删除别人的状态')

@api_view(['POST'])
@login()
def likefeeling(req, pk, is_like):
    item = i_(Feeling, pk)
    if not item: return NOENTITY
    user = User.objects.get(pk=req.session.get('uid'))
    data = dict()
    data['is_like'] = not int(is_like)
    data['name'] = user.name
    data['uid'] = user.id
    data['photo'] = img(user.img)
    if is_like == '0': 
        item.likers.add(user)
        return Response({'code':0, 'msg':'点赞成功', 'data':data})
    else: 
        item.likers.remove(user)
        return Response({'code':0, 'msg':'取消点赞', 'data':data})

@api_view(['GET'])
@login()
def feelinglikers(req, pk, page):
    item = i_(Feeling, pk)
    if not item: return NOENTITY
    queryset = item.likers.all()
    pagesize = settings.FEELINGLIKERS_PAGESIZE
    data = g_feelinglikers(queryset, page, pagesize)
    status = -(len(data)<pagesize)
    return Response({'code':status, 'msg':'', 'data':data})

@api_view(['GET'])
@login()
def feelingcomment(req, pk, page):
    item = i_(Feeling, pk)
    if not item: return NOENTITY
    user = User.objects.get(pk=req.session.get('uid'))
    queryset = Feelingcomment.objects.filter(feeling=item, valid=None)
    pagesize = settings.FEELINGCOMMENT_PAGESIZE
    data = g_feelingcomment(queryset, user, page)
    status = -(len(data)<pagesize)
    return Response({'code':status, 'msg':'', 'data':data})

@api_view(['POST'])
@login()
def postfeelingcomment(req, pk):
    item = i_(Feeling, pk)
    content = req.data.get('content', '').rstrip()
    at = atid = req.data.get('at', None)
    if not item: return NOENTITY
    if not content: return r(1, '回复内容不能为空')
    user = User.objects.get(pk = req.session.get('uid'))
    if at:
        at = i_(Feelingcomment, at)
        if at and user == at.user: return r(1, '不能给自己回复哦')
    obj = Feelingcomment.objects.create(
        feeling = item,
        user = user,
        content = content,
        at = at)
    data = __feelingcomment(obj, user)
    return Response({'code':0, 'msg':'回复成功', 'data':data})

@api_view(['POST'])
@login()
def hidefeelingcomment(req, pk):
    item = i_(Feelingcomment, pk)
    if not item: return NOENTITY
    user = User.objects.get(pk=req.session.get('uid'))
    if item.user == user:
        item.valid = False; item.save()
        return r(0, '删除评论成功')
    return r(0, '不能删除别人的评论')

@api_view(['GET'])
@login()
def background(req):
    user = User.objects.get(pk=s(req))
    if req.method == 'GET':
        data = {'bg': img(user.bg), 'photo': img(user.photo)}
        return Response({'code': 0, 'msg': '', 'data': data})
    elif req.method == 'POST':
        img = req.data.get('file')
        if not img: return r(1, '背景上传失败')
        if imghdr.what(img) not in settings.ALLOW_IMG: return r(1, '图片格式不正确')
        store(user.bg, img) 
        return r(0, '背景设置成功')

@api_view(['GET'])
def test(req):
    return r(0, 'test')
