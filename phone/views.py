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

def isexists(Model, pk):
    model = Model.objects.filter(pk=pk)
    if model.exists(): return model[0]
    return None 

@api_view(['POST'])
def sendcode(request, flag):
    telephone = request.data.get('telephone')
    if validate_telephone(telephone) == False: return Response({'status':1, 'msg':'非法手机号'})
    user = User.objects.filter(telephone=telephone)
    if flag == '0' and user.exists(): return Response({'status':1, 'msg':'该手机注册过, 请直接登录'})
    elif flag == '1' and not user.exists(): return Response({'status':1, 'msg':'您尚未注册, 请先注册'})
    code = random.randint(1000, 9999)
    ret = MobSMS(code).send(telephone)
    if ret == -1: return Response({'status':1, 'msg': '获取验证码失败'})
    request.session[telephone] = code; request.session.set_expiry(60 * 10)
    return Response({'status':0, 'msg':'短息已发送, 请耐心等待'})

@api_view(['POST'])
def register(request):
    telephone = request.data.get('telephone')
    if validate_telephone(telephone) == False:
        return Response({'status':1, 'msg':'手机错误'})
    session_code = request.session.get(telephone)
    if not session_code:
        return Response({'status':1, 'msg':'请获取验证码'})
    if User.objects.filter(telephone=telephone).exists():
        return Response({'status':2, 'msg':'手机已被注册'})
    code = request.data.get('code')
    if code != str(session_code):
        return Response({'status':1, 'msg':'验证码错误'})
    password = request.data.get('password')
    system = request.data.get('system', '').strip()
    if not re.match('^[12]$', system): return ARG
    system = isexists(System, system)
    if not system: return ISEXISTS
    user = User.objects.create(
        telephone=telephone, 
        password=password,
        system = system
    ) 
    request.session[telephone] = ''
    request.session['login'] = user.id; request.session.set_expiry(3600 * 24)
    return Response({'status':0 , 'msg':'注册成功'})

@api_view(['POST'])
def login(request):
    telephone = request.data.get('telephone', '').strip()
    if validate_telephone(telephone) == False:
        return Response({'status':1, 'msg':'手机号码错误'})
    user = User.objects.filter(telephone=telephone)
    if user.exists():
        password = request.data.get('password')
        if password == user[0].password:
            request.session['login'] = user[0].id
            request.session.set_expiry(3600 * 24)
            return Response({'status': 0, 'msg': '登录成功'})
        else:
            return Response({'status': 1, 'msg': '手机或密码错误'})
    return Response({'status':1, 'msg':'您尚未注册,请先注册'})

@api_view(['POST','GET'])        
@islogin()
def regid(request):
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    regid = request.data.get('regid', '').strip()
    if not regid: return myarg('regid') 
    user.regid = regid
    user.save()
    return Response({'status':0, 'msg':'存储reg_id'})

@api_view(['POST', 'GET'])
def logout(request):
    request.session['login'] = ''
    return Response({'status':0, 'msg':'注销登录'})

@api_view(['POST'])
def resetpassword(request):
    telephone = request.data.get('telephone')
    if validate_telephone(telephone) == False:
        return Response({'status':1, 'msg':'手机错误'})
    user = User.objects.filter(telephone=telephone)
    if not user.exists(): return Response({'status':1, 'msg':'手机不存在'})
    code = request.data.get('code')
    code_session = str(request.session[telephone])
    if code != code_session: return Response({'status':1, 'msg':'验证码错误'})
    user = user[0]
    password = request.data.get('password')
    user.password = password
    user.save()
    request.session['login'] = user.id; request.session.set_expiry(3600 * 24)
    request.session[telephone] = ''
    return Response({'status':0, 'msg':'更改密码成功'})

@api_view(['POST'])
@islogin()
def modifypassword(request):
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    if old_password != user.password: return Response({'status':1, 'msg':'旧密码不正确'})
    user.password = new_password
    user.save()
    return Response({'status':0, 'msg':'修改密码成功'})

@api_view(['POST'])
@islogin()
def gender(request):
    gender = request.data.get('gender', '').strip()
    if not re.match('^[01]$', gender): return myarg('gender')
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    user.gender = int(gender)
    user.save()
    return Response({'status':0, 'msg':'性别更改成功'})
            
@api_view(['POST'])
@islogin()
def weixin(request):
    uid = request.data.get('login')
    user = User.objects.get(pk=uid)
    weixin = request.data.get('weixin','').strip()
    if not weixin: return myarg('weixin')
    user.weixin = weixin
    user.save()
    return Response({'status':0, 'msg':'微信更改成功'})

@api_view(['POST'])
@islogin()
def realname(request):
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    name = request.data.get('real_name', '').strip()
    if not name: return myarg('name')
    user.name = name
    user.save()
    return Response({'status':0, 'msg':'姓名更改成功'})

@api_view(['GET', 'POST'])
def banner(rquest):
    banners = Banner.objects.reverse()[:4]
    data = list()
    for banner in banners:
        tmp = dict()
        tmp['img'] = '%s%s' %(RES_URL, banner.img.url)
        tmp['project'] = banner.project.id if banner.project else None
        tmp['url'] = banner.url
        data.append(tmp)
    return Response({'status':0, 'msg': '返回列表', 'data':data})

@api_view(['POST'])
@islogin()
def provincecity(request):
    uid = request.session.get('login')
    province = request.data.get('province', '').strip()
    city = request.data.get('city', '').strip()
    if not province or not city: return myarg('province or city') 
    user = User.objects.get(pk=uid)
    user.province, user.city = province, city
    user.save()
    return Response({'status':0, 'msg': '地区修改成功'})

def project_stage(project):
    now = timezone.now()
    if not project.roadshow_start_datetime:
        stage = {
            'flag': 1,
            'status': '路演预告',
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
                    'status': '路演预告', 
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
                    'status': '融资完毕', 
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
                    'status': '融资进行', 
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
                    'status': '融资进行', 
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
def project(request, page=0):
    ret = g_project( Project.objects.all(), page) 
    return ret

def g_thinktank(queryset, page):
    start, end = start_end(page)
    queryset = queryset[start:end]
    if not queryset: return Response({'status':-1, 'msg':'加载完毕', 'data':[]})
    if isinstance(queryset[0], Thinktank): flag = 't'
    elif isinstance(queryset[0], ThinktankCollect): flag= 'c'
    data = list()
    for item in queryset:
        tmp = dict()
        if flag != 't': item = item.thinktank
        tmp['id'] = item.id
        tmp['img'] = '%s%s' %(RES_URL, item.img.url)
        tmp['thumbnail'] = '%s%s' %(RES_URL, item.img.url)
        tmp['name'] = item.name
        tmp['company'] = item.company
        tmp['title'] = item.title
        tmp['experience'] = item.experience
        data.append(tmp)
    status, msg = (0,'') if len(queryset)==PAGE_SIZE else (-1, '加载完毕')
    return Response({'status':status, 'msg':msg, 'data':data})

@api_view(['POST', 'GET'])
def thinktankdetail(request, pk):
    thinktank = isexists(Thinktank, pk)
    if not thinktank: return ISEXISTS
    data = dict()
    data['url'] = thinktank.video
    data['experience'] = thinktank.experience
    data['success_cases'] = thinktank.success_cases
    data['good_at_field'] = thinktank.good_at_field
    return Response({'status':0, 'msg':'详情', 'data':data})
    
@api_view(['POST', 'GET'])    
def thinktank(request, page):
    ret = g_thinktank(Thinktank.objects.all(), page)
    return ret

@api_view(['POST', 'GET'])
@islogin()
def collectthinktank(request, page):
    uid = request.session.get('login')
    ret = g_thinktank( ThinktankCollect.objects.filter(user__pk=uid), page )
    return ret

def videourl(name):
    q = Auth(settings.access_key, settings.secret_key)
    base_url = 'http://%s/%s' % (settings.bucket_domain, name)
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
@islogin()
def projectdetail(request, pk):
    project = isexists(Project, pk)
    if not project: return ISEXISTS
    data = dict()
    data['company_name'] = project.company.name
    data['stage'] = project_stage(project)
    data['participator2plan'] = project.participator2plan
    data['plan_finance'] = project.planfinance
    data['project_img'] = '%s%s' %(RES_URL, project.img.url)
    data['project_video'] = project.url
    data['url'] = videourl(project.url.split('/')[-1])
    data['invest_amount_sum'] = investamountsum(data['stage']['flag'], project)
    uid = request.session.get('login')
    ls = LikeShip.objects.filter(project__pk=pk)
    data['is_like'] =  ls.filter(user__pk=uid).exists()
    cs = CollectShip.objects.filter(project__pk=pk)
    data['is_collect'] = cs.filter(user__pk=uid).exists()
    ps = ParticipateShip.objects.filter(project__pk=pk)
    data['is_participator'] = ps.filter(user__pk=uid).exists()
    vs = VoteShip.objects.filter(project__pk=pk)
    data['is_vote'] = vs.filter(user__pk=uid).exists()
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
    return Response({'status': 0, 'msg': 'msg', 'data': data})

@api_view(['POST', 'GET'])
def finance_plan(request, pk):
    data = dict()
    project = isexists(Project, pk)
    if not project: return ISEXISTS
    data['plan_finance'] = project.planfinance
    data['finance_pattern'] = project.pattern
    data['share2give'] = project.share2give
    data['fund_purpose'] = project.usage
    data['quit_way'] = project.quitway
    return Response({'status':0, 'msg':'msg', 'data': data})

@api_view(['POST', 'GET'])
def coremember(request, pk):
    project = isexists(Project, pk)
    if not project: return ISEXISTS
    data = list()
    for item in project.coremember_set.all():
        tmp = dict()
        tmp['id'] = item.id
        tmp['img'] = myimg(item.img)
        tmp['name'] = item.name
        tmp['title'] = item.title
        tmp['profile'] = item.profile
        data.insert(0, tmp)
    return Response({'status':0, 'msg':'核心成员', 'data':data})

@api_view(['POST', 'GET'])
def corememberdetail(request, pk):
    coremember = isexists(CoreMember, pk)
    if not coremember: return ISEXISTS
    data = dict()
    data['profile'] = coremember.profile
    return Response({'status':0, 'msg':'核心成员详情', 'data':data})

@api_view(['POST', 'GET'])
def projectinvestorlist(request, pk):
    ivs = InvestShip.objects.filter(project__pk=pk, valid=True)
    data = list()
    for iv in ivs:
        print('lindyang')
        tmp = dict()
        investor = iv.investor
        tmp['certificate_datetime'] = dateformat(investor.certificate_datetime)
        tmp['invest_amount'] = iv.invest_amount
        tmp['real_name'] = investor.user.name
        user = investor.user
        tmp['user_img'] = myimg(user.img)
        data.append(tmp)
    return Response({'status':0, 'msg':'msg', 'data':data})

@api_view(['POST', 'GET'])
def project_event(request, pk):
    pe = ProjectEvent.objects.filter(project__pk=pk)
    data = list()
    for t in pe:
        tmp = dict()
        tmp['event_title'] = t.title
        tmp['event_detail'] = t.detail
        tmp['event_date'] = t.happen_datetime
        data.append(tmp)
    return Response({'status':0, 'msg':'msg', 'data':data})

@api_view(['POST', 'GET'])
@islogin()
def participate(request, pk):
    project = isexists(Project, pk)
    if not project: return ISEXISTS
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    pps = ParticipateShip.objects.filter(project=project, user=user)
    if pps.exists(): return Response({'status':1, 'msg':'已经报名'})
    ParticipateShip.objects.create(project=project, user=user)
    return Response({'status':0, 'msg':'报名成功'})

def g_project(queryset, page): 
    start, end = start_end(page)
    queryset = queryset[start:end]
    if not queryset: return Response({'status':-1, 'msg':'没有项目', 'data':[]})
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
    status, msg = (0, '') if len(queryset)==PAGE_SIZE else (-1, '加载完毕')
    return Response({'status':status, 'msg':msg, 'data':data})

@api_view(['POST', 'GET'])
def recommend_project(request, page):
    ret = g_project( RecommendProject.objects.all(), page )
    return ret

@api_view(['POST', 'GET'])
def wait_for_finance(request, page):
    #ps = Project.objects.filter(roadshow_start_datetime__lt=timezone.now().date()).annotate(invested_sum=Sum('investship__invest_amount')).filter(Q(invested_sum__isnull=True) | Q(invested_sum=0) ) 
    now = timezone.now()
    ret = g_project( Project.objects.filter(roadshow_start_datetime__lte=now, finance_stop_datetime__gte=now), page )
    return ret

@api_view(['POST', 'GET'])
def finish_finance(request, page):
    #ps = Project.objects.annotate(invested_sum=Sum('investship__invest_amount')).filter(invested_sum__gte=F('planfinance'))
    now = timezone.now()
    ret = g_project( Project.objects.filter(finance_stop_datetime__lt = now), page )
    return ret

@api_view(['POST'])
@islogin()
def wantroadshow(request):
    uid = request.session.get('login')
    if Roadshow.objects.filter(~Q(valid=True), user__pk=uid).exists():
        return Response({'status':1, 'msg':'您还有路演申请尚未审核'})
    user = User.objects.get(pk=uid)
    contact_name = request.data.get('contact_name')
    contact_phone = request.data.get('contact_phone')
    company = request.data.get('company')
    vcr = request.data.get('vcr', 'http://baidu.com')
    company = Company.objects.filter(pk=company)
    if not company.exists():
        return Response({'status':1, 'msg':'公司不存在'})
    company = company[0]
    roadshow = Roadshow.objects.create(
                user=user, 
                company=company, 
                contact_name=contact_name, 
                contact_phone=contact_phone,
            )
    return Response({'status':0, 'msg':'申请路演成功, 等待审核', 'data':roadshow.id})

@api_view(['POST', 'GET'])
@islogin()
def activity(request):
    if not Activity.objects.all().exists():
        return Response({'status':-1, 'msg':'目前没有活动'})
    ac = Activity.objects.all()[0]
    if timezone.now() > ac.stop_datetime:
        return Response({'status':-1, 'msg':'目前没有活动'})
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
    return Response({'status':0, 'msg':'置顶活动', 'data':data})

@api_view(['POST', 'GET'])
@islogin()
def signin(request, pk):
    activity = isexists(Activity, pk)
    if not activity: return ISEXISTS
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    if Signin.objects.filter(user=user, activity=activity).exists(): 
        return Response({'status':0, 'msg':'你已经签到'})
    if timezone.now() > activity.stop_datetime: 
        return Response({'status':1, 'msg':'活动结束, 不能签到'})
    Signin.objects.create(user=user, activity=activity)
    return Response({'status':0, 'msg':'签到成功'})

@api_view(['POST'])
@islogin()
def addcompany(request):
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    invalids = JoinShip.objects.filter(~Q(valid=True), user=user)
    if invalids.exists():
        return Response({'status':1, 'msg':'尚有公司在审核中, 请耐心等待'})
    name = request.data.get('company_name')
    company = Company.objects.filter(name=name)
    if company.exists():
        company = company[0]
    else:
        province = request.data.get('province')
        city = request.data.get('city')
        industry= request.data.get('industry_type').split(',')
        companystatus = request.data.get('company_status')
        company = Company.objects.create(
                    name = name,
                    province = province,
                    city = city,
                    companystatus = Companystatus.objects.get(pk=companystatus)
                )
        company.industry= industry

    if not JoinShip.objects.filter(user__pk=uid, company__pk=company.id).exists():
        JoinShip.objects.create(user=user,company=company)
    data = dict()
    data['id'] = company.id
    data['company'] = company.name
    return Response({'status':0, 'msg':'添加公司成功', 'data':data})

@api_view(['POST'])
@islogin()
def editcompany(request, pk):
    return Response({'status':0, 'msg':'修改公司信息'})

@api_view(['POST', 'GET'])
def companyinfo(request, pk):
    company = isexists(Company, pk)
    if not company: return ISEXISTS
    data = dict()
    data['industry_type'] = [it.name for it in company.industry.all()]
    data['province'] = company.province
    data['city'] = company.city
    data['company_status'] = company.companystatus.name
    return Response({'status':0, 'msg':'获取公司信息', 'data':data})

@api_view(['POST', 'GET'])
@islogin()
def mycompanylist(request):
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    cs = user.company.all()
    data = list()
    for c in cs:
        tmp =dict()
        tmp['id'] = c.id
        tmp['company_name'] = c.name
        data.append(tmp)
    return Response({'status':0, 'msg':'我的公司一览表', 'data':data})

@api_view(['POST', 'GET'])
def industry(request):
    its = Industry.objects.all()
    data = list()
    for it in its:
        tmp = dict()
        tmp['id'] = it.id
        tmp['type_name'] = it.name
        data.append(tmp)
    return Response({'status':0, 'msg':'行业一览表', 'data':data})

@api_view(['POST', 'GET'])
def companystatus(request):
    css = Companystatus.objects.all()
    data = list()
    for cs in css:
        tmp = dict()
        tmp['id'] = cs.id
        tmp['status_name'] = cs.name
        data.append(tmp)

    return Response({'status':0, 'msg':'success', 'data':data})

@api_view(['POST', 'GET'])
def investorqualification(request):
    iqs = Qualification.objects.all()
    data = list()
    for iq in iqs:
        tmp = dict()
        tmp['id'] = iq.id
        tmp['desc'] = iq.desc
        data.append(tmp)
    return Response({'status':0, 'msg':'认证条件一览表(多选)', 'data':data})

@api_view(['POST', 'GET'])
def fundsizerange(request):
    fsrs = FundSizeRange.objects.all()
    data = list()
    for fsr in fsrs:
        tmp = dict()
        tmp['id'] = fsr.id
        tmp['desc'] = fsr.desc
        data.append(tmp)
    return Response({'status':0, 'msg':'返回资产情况', 'data':data})

@api_view(['POST', 'GET'])
@islogin()
def authenticate(request):
    uid = request.session.get('login')
    flag = request.data.get('investor_type','').strip()  #认证人的类型
    name = request.data.get('real_name','').strip()
    position = request.data.get('position', '').strip()
    company = request.data.get('company','').strip()
    fundsizerange = request.data.get('fund_size_range', '1').strip()
    qualification = request.data.get('investor_qualification','').strip()
    industry = request.data.get('industry_type', '').strip()
    if not re.match('^[01]$', flag): return ARG
    if not name: return ARG
    if flag == '0' and not position: return ARG
    if flag == '0' and not company: return ARG
    if not PK_RE.match(fundsizerange): return ARG
    if not MTM_RE.match(qualification): return ARG
    if flag == '1' and not MTM_RE.match(industry): return ARG
    if flag == '1':
        company = isexists(Company, company)
        if not company: return ISEXISTS
    else:
        company = None
    fundsizerange = isexists(FundSizeRange, fundsizerange)
    if not fundsizerange: return ISEXISTS
     
    user = User.objects.get(pk=uid)
    investors = Investor.objects.filter(user=user, company=company)

    if investors.exists():
        valid = investors[0].valid
        if valid == None:
            return Response({'status':1, 'msg':'该身份已经认证过, 等待审核中'})
        elif valid == False:
            return Response({'status':1, 'msg':'该身份认证失败'})
        else:
            return Response({'status':1, 'msg':'该身份已经认证成功'})
    
    investor = Investor.objects.create(
         user=user,
         company = company,
         position = position,
         fundsizerange = fundsizerange,
    )
    investor.qualification = qualification.split(',')
    if flag == '0': investor.comment = request.data.get('company').strip() 
    else: investor.industry= industry.split(',')
    investor.save() 
    data = investor.id
    user = User.objects.get(pk=uid)
    user.name = name
    user.save()
    return Response({'status':0, 'msg':'认证成功, 等待审核', 'data':data})

@api_view(['POST', 'GET'])
@islogin()
def businesscard(request, pk):
    investor = Investor.objects.get(pk=pk)
    mystorage_file(
            investor.card,
            request.data.get('file'),
            'investor/%Y/%m'
        )
    return Response({'status':0, 'msg':'上传名片成功'})

@api_view(['POST'])
@islogin()
def idfore(request):
    uid = request.session.get('login')
    upload_file = request.data.get('file')
    user = User.objects.get(pk=uid)
    mystorage_file(user.idfore, upload_file)
    return Response({'status':0, 'msg':'上传身份证成功'})

@api_view(['POST', 'GET'])
@islogin()
def userimg(request):
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    if request.method == 'POST':
        upload_file = request.data.get('file')
        mystorage_file(user.img, upload_file)
        return Response({'status':0, 'msg':'上传图片成功'})
    elif request.method == 'GET':
        data = dict()
        data['img']= myimg(user.img) 
        data['name'] = user.name
        return Response({'status':0, 'msg':'用户头像', 'data':data})

@api_view(['GET','POST'])
def position(request):
    pts = Position.objects.all()
    data = list()
    for pt in pts:
        tmp = dict()
        tmp['id'] = pt.id
        tmp['type_name'] = pt.name
        data.append(tmp)
    return Response({'status':0, 'msg':'职位一览表', 'data':data})

@api_view(['POST'])
@islogin()
def like(request, pk):
    uid = request.session.get('login')
    action = request.data.get('action') 
    if action == '1':
        LikeShip.objects.create(
                user = User.objects.get(pk=uid),
                project = Project.objects.get(pk=pk)
            )
        return Response({'status':0, 'msg':'点赞成功'})
    else:
        LikeShip.objects.filter(
                user__pk=uid,
                project__pk=pk
            ).delete()
        return Response({'status':0, 'msg':'取消点赞'})

@api_view(['POST'])
@islogin()
def vote(request, pk): 
    project = isexists(Project, pk)
    if not project: return ISEXISTS
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    if VoteShip.objects.filter(project=project, user=user).exists():
        return Response({'status':0, 'msg':'您已经投票成功'})
    VoteShip.objects.create(
        project = project,
        user = user 
    )
    return Response({'status':0, 'msg':'投票成功'})


@api_view(['POST'])
@islogin()
def collect(request, pk):
    uid = request.session.get('login')
    action = request.data.get('action') 
    if action == '1':
        CollectShip.objects.create(
                user = User.objects.get(pk=uid),
                project = Project.objects.get(pk=pk)
            )
        return Response({'status':0, 'msg':'收藏成功'})
    else:
        CollectShip.objects.filter(
                user__pk=uid,
                project__pk=pk
            ).delete()
        return Response({'status':0, 'msg':'取消收藏'})

@api_view(['POST'])
@islogin()
def modifyposition(request):
    position = request.data.get('position_type', '').strip()
    if not MTM_RE.match(position): return ARG
    uid = request.session.get('login')
    User.objects.get(pk=uid).position = position.split(',')
    return Response({'status':0, 'msg':'修改职位成功'})

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
@islogin()
def collectfinancing(request, page):
    uid = request.session.get('login')
    now = timezone.now()
    queryset = CollectShip.objects.filter(
            user__pk=uid, 
            project__roadshow_start_datetime__lte=now, 
            project__finance_stop_datetime__gte=now,
        )
    ret = g_project( queryset, page )
    return ret

@api_view(['GET', 'POST'])
@islogin()
def collectfinanced(request, page):
    uid = request.session.get('login')
    now = timezone.now()
    queryset = CollectShip.objects.filter(
            user__pk=uid,
            project__finance_stop_datetime__lt=now
        )
    ret = g_project( queryset, page )
    return ret

@api_view(['GET', 'POST'])
@islogin()
def collectroadshow(request, page=0):
    uid = request.session.get('login')
    now = timezone.now()
    queryset = CollectShip.objects.filter(
        Q(project__roadshow_start_datetime__isnull=True) | 
        Q(project__roadshow_start_datetime__gt=now),
        user__pk=uid, 
    )
    ret = g_project( queryset, page )
    return ret

@api_view(['POST', 'GET'])
@islogin()
def feedback(request):
    uid = request.session.get('login')
    advice = request.data.get('advice', '').strip()
    if not advice: return ARG
    if Feedback.objects.filter(user__pk=uid, valid=None).exists():
        return Response({'status':0, 'msg':'你尚有反馈在处理中'})
    Feedback.objects.create(
        user = User.objects.get(pk=uid),
        advice = advice
    )
    return Response({'status':0, 'msg':'反馈成功, 请耐心等待'})

@api_view(['GET', 'POST'])
def keyword(request):
    industrys = Industry.objects.filter(~Q(valid=False))
    data = list()
    for keyword in industrys:
        tmp = dict()
        tmp['id'] = keyword.id
        tmp['word'] = keyword.name
        data.append(tmp)
    return Response({'status':0, 'msg':'热词一览表', 'data':data})

@api_view(['POST', 'GET'])
def projectsearch(request, pk, page):
    if pk == '0': 
        value = request.data.get('value').strip()
        if not value: return myarg('value')
        queryset = Project.objects.filter(company__name__contains=value)
    else: queryset = Project.objects.filter(company__industry__in=[int(pk),])
    ret = g_project(queryset, page)
    return ret

@api_view(['GET', 'POST'])
@islogin()
def generalinformation(request):
    uid = request.session.get('login')
    data = dict()
    data['telephone'] = User.objects.get(pk=uid).telephone
    user = User.objects.get(pk=uid)
    data['user_img'] = myimg(user.img)
    data['real_name'] = user.name
    data['gender'] = user.gender
    data['position_type'] = [pt.name for pt in user.position.all()]
    #data['province_city'] = [user.province, user.city]
    data['province'] = user.province
    data['city'] = user.city
    return Response({'status':0, 'msg':'用户信息', 'data':data})

@api_view(['POST', 'GET'])
@islogin()
def myinvestorlist(request):
    uid = request.session.get('login')
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
    return Response({'status':0, 'msg':'我的投资列表', 'data':data})
        
@api_view(['GET', 'POST'])
@islogin()
def wantinvest(request, pk):
    flag = request.data.get('flag','').strip()
    if not re.match('^[01]$', flag): return ARG
    invest_amount = request.data.get('invest_amount', '').strip() # 投资金额
    if not PK_RE.match(invest_amount): return ARG
    investor = request.data.get('investor', '').strip() # 投资人id
    if not PK_RE.match(investor): 
        return  Response({'status':1, 'msg':'请点击选择您的投资人身份'})
        return ARG 
    project = isexists(Project, pk) # 项目
    if not project: return ISEXISTS
    fund = project.leadfund if flag=='1' else project.followfund
    if int(invest_amount) < fund:
        return Response({'status':1, 'msg':'金额必须大于%s' % fund})
    uid = request.session.get('login')
    investor_obj = Investor.objects.filter(pk=investor, user__pk=uid) # 投资人实体
    if not investor_obj.exists():
        return Response({'status':-9, 'msg':'该投资人不存在'})
    investship = InvestShip.objects.filter(project__pk=pk, investor__pk=investor) #是否投资过
    if investship.exists():
        return Response({'status':1, 'msg':'您已经投资过该项目'})
    InvestShip.objects.create(
        investor = investor_obj[0],
        project = project,
        invest_amount = invest_amount,
        lead = int(flag)
    )
    return Response({'status':0, 'msg':'投资成功'})

@api_view(['GET', 'POST'])
@islogin()
def myinvestorauthentication(request):
    uid = request.session.get('login')
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
            tmp['reject_reason'] = '等待审核, 预计在提交的2天内处理'
        data.append(tmp)
    return Response({'status':0, 'msg':'我的投资认证一览表', 'data':data})

@api_view(['GET', 'POST'])
@islogin()
def myroadshow(request):
    uid = request.session.get('login')
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
            tmp['reason'] = '等待审核, 预计在提交的2天内处理'
        data.append(tmp)
    return Response({'status':0, 'msg':'路演申请一览表', 'data':data})

@api_view(['GET', 'POST'])
@islogin()
def myparticipate(request):
    uid = request.session.get('login')
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
            tmp['reason'] = '等待审核, 预计在提交的2天内处理'
        data.append(tmp)
    return Response({'status':0, 'msg':'我的来现场一览表', 'data':data})

@api_view(['GET', 'POST'])
@islogin()
def mycreateproject(request, page):
    uid = request.session.get('login')
    print('lindyang')
    ret = g_project( Project.objects.filter(roadshow__user__isnull=False, roadshow__user__pk=uid), page )
    return ret

@api_view(['GET', 'POST'])
@islogin()
def myinvestproject(request, page):
    uid = request.session.get('login')
    ret = g_project( InvestShip.objects.filter(investor__user__pk=uid), page )
    return ret

@api_view(['POST', 'GET'])
@islogin()
def token(request):
    key = request.data.get('key','').strip()
    print(key, 'key1')
    if not key:
        return Response({'status':1, 'msg':'key不能为空'})
    print(key, 'key')
    q = Auth(settings.access_key, settings.secret_key)
    token = q.upload_token(settings.bucket_name, key)
    uid = request.session.get('login')
    token2 = q.upload_token(settings.bucket_name, 
            key, 
            7200, 
            {'callbackUrl':'http://115.28.177.22/phone/callback/', 
            'callbackBody':'name=$(fname)&hash=$(etag)',
            #'callbackBodyType':'application/json'
            }
        )
    return Response({'start':0, 'msg':'token', 'data':token2})

@api_view(['POST', 'GET'])
def callback(request):
    name = request.data.get('name')
    print(request.data)
    print(name, '视频名')
    q = Auth(settings.access_key, settings.secret_key)
    base_url = 'http://%s/%s' % (settings.bucket_domain, name)
    private_url = q.private_download_url(base_url, expires=3600)
    print(private_url)
    return Response({'status':0, 'msg':'视频上传成功', 'data':private_url})

@api_view(['POST', 'GET'])
def qiniudelete(request):
    key = ''
    q = Auth(settings.access_key, settings.secret_key)
    bucket = BucketManager(q)
    ret, info = bucket.delete(settings.bucket_name, key)
    print(info)
    assert ret is None
    assert info.status_code == 612
    

@api_view(['POST', 'GET'])
@islogin()
def urlsave(request, pk):
    roadshow = Roadshow.objects.filter(pk=pk)
    if not roadshow.exists(): return Response({'status':1, 'msg':'路演项目不存在'})
    roadshow = roadshow[0]
    roadshow.vcr = vcr
    roadshow.save()
    return Response({'status':0, 'msg':'路演视频关联'})

@api_view(['POST', 'GET'])
@islogin()
def deletevideo(request):
    key = request.data.get('key','').strip()
    if not key: return Response({'status':1, 'msg':'参数错误'})
    q = Auth(settings.access_key, settings.secret_key)
    bucket = BucketManager(q)
    ret, info = bucket.delete(settings.bucket_name, key)
    assert ret is None
    assert info.status_code == 612
    return Response({'status':0, 'msg':'删除视频成功'})

@api_view(['POST', 'GET'])
@islogin()
def ismyproject(request, pk):
    project = isexists(Project, pk)
    if not project: return ISEXISTS
    uid = request.session.get('login')
    if project.roadshow and  project.roadshow.user.id == uid: 
        return Response({'status':1, 'msg':'你不可以给自己的项目投资'})
    return Response({'status':0, 'msg':'可以投资'})

@api_view(['POST', 'GET'])
@islogin()
def isinvestor(request):
    uid = request.session.get('login')
    investors = Investor.objects.filter(user__pk=uid)
    if not investors.exists():
        return Response({'status':-9, 'msg':'您还没有认证'})
    elif investors.filter(valid=True).exists():
        return Response({'status':0, 'msg':'您已经认证'})
    elif investors.filter(valid=None).exists():
        return Response({'status':1, 'msg':'您认证在审核中'})
    else:
        return Response({'status':1, 'msg':'您认证失败'})

@api_view(['POST', 'GET'])
@islogin()
def investorinfo(request, pk):
    investor = isexists(Investor, pk)
    if not investor: return ISEXISTS
    data = dict()
    data['investor_type'] = 1 if investor.company else 0 
    if investor.company: #机构投资人
        data['company'] = investor.company.name
        data['industry'] = [it.name for it in investor.industry.all()]
        data['fund_size_range'] = investor.fundsizerange.desc
    else: #自然投资人
        user = investor.user
        data['real_name'] = user.name
        data['telephone'] = investor.user.telephone
        data['province'] = user.province
        data['city'] = user.city
        data['company'] = investor.comment
        data['position'] = investor.position
    return Response({'status':0, 'msg':'投资人信息', 'data':data})

@api_view(['POST'])
@islogin()
def issessionvalid(request):
    return Response({'status':0, 'msg':'session合法'})

@api_view(['POST', 'GET'])
def contactus(request):
    data = {
        'telephone':settings.Michael,
        'name':'徐力'
    }
    return Response({'status':0, 'msg':'联系我们', 'data':data})

@api_view(['POST', 'GET'])
def checkupdate(request, system):
    return Response({'status':1, 'msg':'没有更新'})
    queryset = Version.objects.filter(system__id=system)
    if not queryset: 
        return Response({'status':0, 'msg':'没有更新'})
    version = queryset[0] 
    data = dict()
    data['force'] = True #False
    data['edition'] = version.edition
    data['item'] = version.item
    data['href'] = version.href 
    return Response({'status':0, 'msg':'检查更新', 'data':data})

@api_view(['POST', 'GET'])
def shareproject(request, pk):
    data = dict()
    data['title'] = '项目分享'
    data['img'] = '%s/static/app/img/icon.png' % settings.RES_URL
    data['url'] = 'http://www.jinzht.com:80'
    data['content'] = '项目分享'
    return Response({'status':0, 'msg':'分享', 'data':data})

@api_view(['POST', 'GET'])
def shareapp(request):
    data = dict()
    data['title'] = 'app分享'
    data['img'] = '%s/static/app/img/icon.png' % settings.RES_URL
    data['url'] = 'http://www.jinzht.com:80'
    data['content'] = '金指投App分享'
    return Response({'status':0, 'msg':'分享', 'data':data})

def document(name):
    cur_dir = os.path.dirname(__file__)
    f = os.path.join(cur_dir, 'document/%s' %name )
    if not os.path.exists(f):
        return Response({'status':0, 'msg':'没有数据', 'data':'no data'})

    import codecs
    with codecs.open(f, 'r', 'utf-8') as fp:
        data = fp.read()
        return Response({'status':0, 'msg':'协议', 'data':data})

@api_view(['POST', 'GET'])
def privacy(request):
    return document('privacy')

@api_view(['POST', 'GET'])
def aboutroadshow(request):
    return document('aboutroadshow')

@api_view(['POST', 'GET'])
def risk(request):
    return document('risk')

@api_view(['POST', 'GET'])
def useragreement(request):
    return document('useragreement')

@api_view(['POST', 'GET'])
def projectprotocol(request):
    return document('projectprotocol')

@api_view(['POST', 'GET'])
def crowfunding(request):
    return document('crowfunding')

@api_view(['POST', 'GET'])
def leadfunding(request):
    return document('leadfunding')

@api_view(['POST', 'GET'])
@islogin()
def topic(request, pk):
    content = request.data.get('content','')
    if content.strip() == '': return myarg('content') 
    project = isexists(Project, pk)
    if not project: return ISEXISTS
    at_topic = request.data.get('at_topic',0)
    if not at_topic: 
        at_topic = None
        msg = '发表话题成功'
    else: 
        at_topic = isexists(Topic, at_topic)
        msg = '回复成功'
    uid = request.session.get('login')
    user = User.objects.get(pk=uid) 
    if at_topic and at_topic.user == user:
        print(at_topic.user)
        print(user)
        return Response({'status':1, 'msg':'不能给自己回复哦'})
    topic = Topic.objects.create(
       project = project,
       user = user,
       at_topic = at_topic,
       content = content,
    )
    return Response({'status':0, 'msg':msg, 'data':topic.id})

def g_topiclist(queryset, page, at=True):
    start, end = start_end(page, 6)
    queryset = queryset[start:end]
    data = list()
    for item in queryset:
        tmp = dict()
        tmp['pid'] = item.project.id
        tmp['id'] = item.id
        tmp['img'] = myimg(item.user.img)
        if item.at_topic: 
            if at == True:
                tmp['name'] = '%s@%s' % (item.user.name, item.at_topic.user.name)
            else:
                tmp['name'] = '%s 回复了您' % (item.user.name)
        else: tmp['name'] = '%s' % (item.user.name)
        tmp['create_datetime'] = datetime_filter(item.create_datetime) 
        tmp['content'] = item.content
        tmp['investor'] = Investor.objects.filter(user=item.user, valid=True).exists()
        data.append(tmp) 
    status, msg = (0,'') if len(queryset)==6 else (-1, '加载完毕')
    return Response({'status':status, 'msg':msg, 'data':data})

@api_view(['POST', 'GET'])
@islogin()
def topiclist(request, pk, page):
    queryset = Topic.objects.filter(project__pk=pk)
    ret = g_topiclist(queryset, page)
    return ret
   
def g_news(queryset, page):
    start, end = start_end(page)
    queryset = queryset[start:end]
    if not queryset and int(page) == 0: return Response({'status':0, 'msg':'没有相关数据'})
    data = list()
    for item in queryset:
        tmp = dict()
        tmp['id'] = item.id
        tmp['title'] = item.title
        tmp['source'] = item.source
        tmp['content'] = item.content
        tmp['src'] = item.src
        tmp['sharecount'] = item.sharecount
        tmp['create_datetime'] = datetime_filter(item.create_datetime) 
        tmp['create_datetime'] = timezone.localtime(item.create_datetime).strftime('%m/%d %H:%M')
        tmp['readcount'] = item.readcount
        tmp['href'] = '%s/%s/%s' %(settings.RES_URL, settings.NEWS_URL_PATH, item.name)
        data.append(tmp)
    status, msg = (0, '') if len(queryset) == PAGE_SIZE else (-1, '加载完毕')
    return Response({'status': status, 'msg':msg, 'data':data})

@api_view(['POST', 'GET'])
def news(request, pk, page):
    queryset = News.objects.filter(newstype__id=pk)
    return g_news(queryset, page)

@api_view(['POST', 'GET'])
def knowledge(request, page):
    queryset = News.objects.filter(newstype=4)
    return g_news(queryset, page)

@api_view(['POST', 'GET'])
def sharenews(request, pk):
    news = isexists(News, pk) 
    if not news: return ISEXISTS 
    data = dict()
    data['href'] = '%s/%s/%s' %(settings.RES_URL, settings.NEWS_URL_PATH, news.name)
    data['src'] = news.src 
    data['title'] = news.title
    data['content'] = news.content
    return Response({'status':0, 'msg':'newsshare', 'data':data})

@api_view(['POST', 'GET'])
def newssharecount(request, pk):
    news = isexists(News, pk) 
    if not news: return ISEXISTS 
    news.sharecount += 1
    news.save()
    return Response({'status':0, 'msg':'分享数加'})
        
@api_view(['POST', 'GET'])
def newsreadcount(request, pk):
    news = isexists(News, pk) 
    if not news: return ISEXISTS 
    news.readcount += 1
    news.save()
    return Response({'status':0, 'msg':'阅读数加'})
    
@api_view(['POST', 'GET'])
def newssearch(request, pk, page):
    value = request.data.get('value', '').strip()
    if not value: return myarg('value')
    if pk == '0': queryset = News.objects.filter(title__contains=value)
    else: queryset = News.objects.filter(newstype__id=pk)
    return g_news(queryset, page)

@api_view(['POST', 'GET'])
def newstype(request):
    data = [{'key':item.id, 'value':item.name} for item in NewsType.objects.filter(~Q(valid=False))]
    return Response({'status':0, 'msg':'newstag', 'data':data})

@api_view(['POST', 'GET'])
def knowledgetag(request):
    data = []
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
@islogin()
def hassysteminform(request):
    uid = request.session.get('login')
    queryset = SystemInform.objects.filter(user__pk=uid, read=False)
    data = {'count': queryset.count()}
    return Response({'status':0, 'msg':'系统消息', 'data':data})    

@api_view(['POST', 'GET'])
@islogin()
def systeminform(request, page):
    uid = request.session.get('login')
    queryset = SystemInform.objects.filter(user__pk=uid)
    start, end = start_end(page)
    queryset = queryset[start:end]
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
    return Response({'status':0, 'msg':'系统通知', 'data':data})

@api_view(['POST', 'GET'])
@islogin()
def setsysteminform(request, pk):
    systeminform = isexists(SystemInform, pk)
    if not systeminform: return myarg('systeminform')
    systeminform.read = True
    systeminform.save()
    return Response({'status':0, 'msg':'设置消息已读', 'data':systeminform.read})

@api_view(['POST', 'GET'])
@islogin()
def deletesysteminform(request, pk):
    systeminform = isexists(SystemInform, pk)
    if not systeminform: return myarg('systeminform')
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    if systeminform.user == user:
        systeminform.delete()
        return Response({'status':0, 'msg':'删除msg'})
    return Response({'status': 1, 'msg':'不能删除别人的msg啊'})

@api_view(['POST', 'GET'])
@islogin()
def hasnewtopic(request):
    uid = request.session.get('login') 
    queryset = Topic.objects.filter(at_topic__user__id=uid, read=False)
    return Response({'status':0, 'msg':'', 'data':{'count':queryset.count()}})

@api_view(['POST', 'GET'])
@islogin()
def topicread(request, page):
    uid = request.session.get('login') 
    queryset = Topic.objects.filter(~Q(read=None), at_topic__user__id=uid) 
    ret = g_topiclist(queryset, page, False)
    return ret

@api_view(['POST', 'GET'])
@islogin()
def settopicread(request, pk):
    uid = request.session.get('login')
    if pk == '0':
        queryset = Topic.objects.filter(at_topic__user__id=uid, read=False) 
        queryset.update(read=True)
        return Response({'status':0, 'msg':'全部设为已读'})
    topic = isexists(Topic, pk)
    if not topic: return myarg('topic')
    topic.read = None 
    topic.save()
    return Response({'status':0, 'msg':'删除成功'})

@api_view(['POST', 'GET'])
def latestnewscount(request):
    yesterday = timezone.now() - timedelta(days=1)
    queryset = News.objects.filter(~Q(newstype=4), create_datetime__gt=yesterday)
    return Response({'status':0, 'msg':'新三板数量', 'data':{'count':queryset.count()}})
    
@api_view(['POST', 'GET'])
def latestknowledgecount(request):
    yesterday = timezone.now() - timedelta(days=1)
    queryset = News.objects.filter(newstype=4, create_datetime__gt=yesterday)
    return Response({'status':0, 'msg':'新三板数量', 'data':{'count':queryset.count()}})

def g_feelinglist(queryset, page):
    start, end = start_end(page, 6)
    queryset = queryset[start:end]
    data = list()
    for item in queryset:
        tmp = dict()
        tmp['id'] = item.id
        tmp['photo'] = myimg(item.user.img)
        tmp['content'] = item.content
        pics = item.pics.all()
        _queryset = Feelingcomment.objects.filter(feeling=item)
        _data = list()
        for _item in _queryset:
            _tmp = dict()
            _tmp['id'] = _item.id
            _tmp['phote'] = myimg(_item.user.img)
            if _item.at:
                _tmp['name'] = '%s@%s' % (_item.user.name, _item.at.user.name)
            else:
                _tmp['name'] = '%s' % (_item.user.name)
            _tmp['content'] = '%s' % (_item.content)
            _data.append(_tmp)
        tmp['_data'] = _data
        data.append(tmp)
    return Response({'status':0, 'msg':'状态圈', 'data':data})

@api_view(['POST'])
@islogin()
def feeling(request, page):
    queryset = Feeling.objects.all()
    ret = g_feelinglist(queryset, page)
    return ret

@api_view(['POST'])
@islogin()
def postfeeling(request):
    #files = dict(request.data).get('file', None)
    #if not files: return Response({'stauts':1, 'msg':'没有图片上传'})
    #pth = os.path.join(settings.BASE_DIR, 'media/feeling')
    #for file in files:
    #    filename = '{}{}'.format(uuid.uuid4().hex, '.png')
    #    filepath = os.path.join(pth, filename)
    #    print(filepath)
    #    with codecs.open(filepath, 'w+', 'utf-8') as f:
    #        f.write(file)
    pth = os.path.join(settings.BASE_DIR, 'media/feeling')
    print(request.FILES)
    for i in range(0, 9):
        img = request.data.get('file%s' %i, None)
        if not img: continue
        if type(img) == str:
            img = File(img)
        filename = '{}{}'.format(uuid.uuid4().hex, '.png')
        filepath = os.path.join(pth, filename)
        fp = open(filepath, 'wb')
        for out in img.chunks():
            fp.write(out)
        fp.close()
        print(filepath)
    #uid = request.session.get('login')
    return Response({'status':0, 'msg':'postfeeling'})

@api_view(['POST', 'GET'])
@islogin()
def deletefeeling(request, pk):
    item = isexists(Feeling, pk)
    if not item: return ISEXISTS
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    if item.user == user:
        item.delete()
        return Response({'status':0, 'msg':'删除状态成功'})
    return Response({'status':0, 'msg':'不能删除别人的状态'})

@api_view(['POST'])
@islogin()
def likefeeling(request, pk, flag):
    item = isexists(Feeling, pk)
    if not item: return ISEXISTS
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    if flag == '1':
        item.likers.add(user)
    else:
        item.likers.remove(user)
    return Response({'status':0, 'msg':'操作成功'})

@api_view(['GET'])
@islogin()
def feelinglikers(request, pk):
    item = isexists(Feeling, pk)
    if not item: return ISEXISTS
    data = '.'.join( item.likers.all() )
    return Response({'status':0, 'msg':'状态点赞情况', 'data':data})

@api_view(['POST'])
@islogin()
def postfeelingcomment(request, pk):
    item = isexists(Feeling, pk)
    if not item: return ISEXISTS
    uid = request.session.get('login') 
    content = request.data.get('content', '').rstrip()
    at = request.data.get('at', 0)
    if not at: at = None
    else: at = isexists(Feeling, at)
    Feelingcomment.objects.create(
        feeling = item,
        user = User.objects.get(pk=uid),
        content = content,
        at = at
    )
    return Response({'status':0, 'msg':'回复成功'})

@api_view(['POST'])
@islogin()
def deletefeelingcomment(request, pk):
    item = isexists(Feeling, pk)
    if not item: return ISEXISTS
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    if item.user == user:
        item.delete()
        return Response({'status':0, 'msg':'删除评论'})
    return Response({'status':0, 'msg':'不能删除别人的评论'})
