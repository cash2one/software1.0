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

NOENTITY = Response({'status':1, 'msg':'no entity'})
def getinstance(Model, pk):
    model = Model.objects.filter(pk=pk)
    return model[0] if model.exists() else None

@api_view(['POST'])
def sendcode(request, flag):
    telephone = request.data.get('telephone')
    if validate_telephone(telephone) == False: return Response({'status':1, 'msg':'手机格式不正确'})
    user = User.objects.filter(telephone=telephone)
    if flag == '0' and user.exists(): return Response({'status':1, 'msg':'该手机已注册, 请直接登录'})
    elif flag == '1' and not user.exists(): return Response({'status':1, 'msg':'您尚未注册, 请先注册'})
    code = random.randint(1000, 9999)
    ret = MobSMS(code).send(telephone)
    if ret == -1: return Response({'status':1, 'msg': '获取验证码失败'})
    request.session[telephone] = code; request.session.set_expiry(60 * 10)
    return Response({'status':0, 'msg':'短信验证码已发送, 请耐心等待'})

@api_view(['POST'])
def register(request):
    telephone = request.data.get('telephone')
    if validate_telephone(telephone) == False:
        return Response({'status':1, 'msg':'手机格式不正确'})
    session_code = request.session.get(telephone)
    if not session_code:
        return Response({'status':1, 'msg':'请先获取验证码'})
    if User.objects.filter(telephone=telephone).exists():
        return Response({'status':2, 'msg':'您的手机号码已注册, 请直接登录'})
    code = request.data.get('code')
    if code != str(session_code):
        return Response({'status':1, 'msg':'验证码错误'})
    password = request.data.get('password')
    system = request.data.get('system', '').strip()
    if not re.match('^[12]$', system): return ARG
    system = getinstance(System, system)
    if not system: return NOENTITY
    user = User.objects.create(
        telephone=telephone, 
        password=password,
        system = system
    ) 
    request.session[telephone] = ''
    request.session['login'] = user.id; request.session.set_expiry(3600 * 24)
    return Response({'status':0 , 'msg':'恭喜您, 注册成功!'})

@api_view(['POST'])
def login(request):
    telephone = request.data.get('telephone', '').strip()
    if validate_telephone(telephone) == False:
        return Response({'status':1, 'msg':'手机格式不正确'})
    user = User.objects.filter(telephone=telephone)
    if user.exists():
        password = request.data.get('password')
        if password == user[0].password:
            request.session['login'] = user[0].id
            request.session.set_expiry(3600 * 24)
            return Response({'status': 0, 'msg': '登录成功'})
        else:
            return Response({'status': 1, 'msg': '手机号码或密码错误'})
    return Response({'status':1, 'msg':'您尚未注册, 请先注册'})

@api_view(['POST','GET'])        
@islogin()
def regid(request):
    user = User.objects.get(pk=request.session.get('login'))
    regid = request.data.get('regid', '').strip()
    if not regid: return myarg('regid') 
    user.regid = regid; user.save()
    return Response({'status':0, 'msg':''})

@api_view(['POST', 'GET'])
def logout(request):
    request.session['login'] = ''
    return Response({'status':0, 'msg':'退出成功'})

@api_view(['POST'])
def resetpassword(request):
    telephone = request.data.get('telephone')
    if validate_telephone(telephone) == False: return Response({'status':1, 'msg':'手机格式不正确'})
    user = User.objects.filter(telephone=telephone)
    if not user.exists(): return Response({'status':1, 'msg':'您尚未注册, 请先注册'})
    code = request.data.get('code')
    code_session = str(request.session[telephone])
    if code != code_session: return Response({'status':1, 'msg':'验证码错误'})
    user = user[0]
    password = request.data.get('password')
    user.password = password; user.save()
    request.session['login'] = user.id; request.session.set_expiry(3600 * 24)
    request.session[telephone] = ''
    return Response({'status':0, 'msg':'设置密码成功'})

@api_view(['POST'])
@islogin()
def modifypassword(request):
    user = User.objects.get(pk=request.session.get('login'))
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    if old_password != user.password: return Response({'status':1, 'msg':'旧密码输入有误'})
    user.password = new_password; user.save()
    return Response({'status':0, 'msg':'修改密码成功'})

@api_view(['POST'])
@islogin()
def gender(request):
    gender = request.data.get('gender', '').strip()
    if not re.match('^[01]$', gender): return myarg('gender')
    user = User.objects.get(pk=request.session.get('login'))
    user.gender = int(gender); user.save()
    return Response({'status':0, 'msg':'性别设置成功'})
            
@api_view(['POST'])
@islogin()
def weixin(request):
    weixin = request.data.get('weixin','').strip()
    if not weixin: return myarg('weixin')
    user = User.objects.get(pk=request.session.get('login'))
    user.weixin = weixin; user.save()
    return Response({'status':0, 'msg':'微信设置成功'})

@api_view(['POST'])
@islogin()
def realname(request):
    name = request.data.get('real_name', '').strip()
    if not name: return myarg('name')
    user = User.objects.get(pk=request.session.get('login'))
    user.name = name; user.save()
    return Response({'status':0, 'msg':'姓名设置成功'})

@api_view(['GET', 'POST'])
def banner(rquest):
    queryset= Banner.objects.reverse()[:4]
    data = list()
    for item in queryset:
        tmp = dict()
        tmp['img'] = '%s%s' %(RES_URL, item.img.url)
        tmp['project'] = item.project.id if item.project else None
        tmp['url'] = item.url
        data.append(tmp)
    return Response({'status':0, 'msg': '', 'data':data})

@api_view(['POST'])
@islogin()
def provincecity(request):
    province = request.data.get('province', '').strip()
    city = request.data.get('city', '').strip()
    if not province or not city: return myarg('province or city') 
    user = User.objects.get(pk=request.session.get('login'))
    user.province, user.city = province, city; user.save()
    return Response({'status':0, 'msg': '地区设置成功'})

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

@api_view(['POST', 'GET'])
def thinktankdetail(request, pk):
    item = getinstance(Thinktank, pk)
    if not item: return NOENTITY
    data = dict()
    data['url'] = item.video
    data['experience'] = item.experience
    data['success_cases'] = item.success_cases
    data['good_at_field'] = item.good_at_field
    return Response({'status':0, 'msg':'', 'data':data})
    
@api_view(['POST', 'GET'])    
def thinktank(request, page):
    queryset = g_queryset(Thinktank.objects.all(), page)
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
    return Response({'status':status, 'msg':'加载完毕', 'data':data})

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
#@islogin()
def projectdetail(request, pk):
    project = getinstance(Project, pk)
    if not project: return NOENTITY
    data = dict()
    data['company_name'] = project.company.name
    data['stage'] = project_stage(project)
    data['participator2plan'] = project.participator2plan
    data['plan_finance'] = project.planfinance
    data['project_img'] = '%s%s' %(RES_URL, project.img.url)
    data['project_video'] = project.url or createurl(project.roadshow.vcr if project.roadshow else '')
    data['invest_amount_sum'] = investamountsum(data['stage']['flag'], project)
    uid = request.session.get('login')
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
    return Response({'status': 0, 'msg': '', 'data': data})

@api_view(['POST', 'GET'])
def financeplan(request, pk):
    item = getinstance(Project, pk)
    if not item: return NOENTITY
    data = dict()
    data['plan_finance'] = item.planfinance
    data['finance_pattern'] = item.pattern
    data['share2give'] = item.share2give
    data['fund_purpose'] = item.usage
    data['quit_way'] = item.quitway
    return Response({'status':0, 'msg':'', 'data': data})

@api_view(['POST', 'GET'])
def coremember(request, pk):
    project = getinstance(Project, pk)
    if not project: return NOENTITY
    data = list()
    queryset = project.coremember_set.all()
    for item in queryset:
        tmp = dict()
        tmp['id'] = item.id
        tmp['img'] = myimg(item.img)
        tmp['name'] = item.name
        tmp['title'] = item.title
        tmp['profile'] = item.profile
        data.insert(0, tmp)
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def corememberdetail(request, pk):
    coremember = getinstance(CoreMember, pk)
    if not coremember: return NOENTITY
    data = dict()
    data['profile'] = coremember.profile
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def projectinvestorlist(request, pk):
    queryset = InvestShip.objects.filter(project__pk=pk, valid=True)
    data = list()
    for item in queryset:
        tmp = dict()
        investor = item.investor
        user = investor.user
        tmp['certificate_datetime'] = dateformat(investor.certificate_datetime)
        tmp['invest_amount'] = item.invest_amount
        tmp['real_name'] = user.name
        tmp['user_img'] = myimg(user.img)
        data.append(tmp)
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def projectevent(request, pk):
    queryset = ProjectEvent.objects.filter(project__pk=pk)
    data = list()
    for item in queryset:
        tmp = dict()
        tmp['event_title'] = item.title
        tmp['event_detail'] = item.detail
        tmp['event_date'] = item.happen_datetime
        data.append(tmp)
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
@islogin()
def participate(request, pk):
    project = getinstance(Project, pk)
    if not project: return NOENTITY
    user = User.objects.get(pk=request.session.get('login'))
    item = ParticipateShip.objects.filter(project=project, user=user)
    if item.exists(): return Response({'status':1, 'msg':'您已申请参加该项目路演, 无需重复报名'})
    ParticipateShip.objects.create(project=project, user=user)
    return Response({'status':0, 'msg':'恭喜您, 申请成功'})

@api_view(['GET'])
def defaultclassify(request): return Response({'status':0, 'msg':'', 'data':0})

def g_project(queryset, page): 
    queryset = g_queryset(queryset, page)
    if not queryset: return Response({'status':-1, 'msg':'加载完毕', 'data':[]})
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
    return Response({'status':status, 'msg':'加载完毕', 'data':data})

@api_view(['POST', 'GET'])
def recommendproject(request, page):
    ret = g_project( RecommendProject.objects.all(), page )
    return ret

@api_view(['POST', 'GET'])
def waitforfinance(request, page):
    #ps = Project.objects.filter(roadshow_start_datetime__lt=timezone.now().date()).annotate(invested_sum=Sum('investship__invest_amount')).filter(Q(invested_sum__isnull=True) | Q(invested_sum=0) ) 
    now = timezone.now()
    ret = g_project( Project.objects.filter(roadshow_start_datetime__lte=now, finance_stop_datetime__gte=now), page )
    return ret

@api_view(['POST', 'GET'])
def finishfinance(request, page):
    #ps = Project.objects.annotate(invested_sum=Sum('investship__invest_amount')).filter(invested_sum__gte=F('planfinance'))
    now = timezone.now()
    ret = g_project( Project.objects.filter(finance_stop_datetime__lt = now), page )
    return ret

@api_view(['POST'])
@islogin()
def wantroadshow(request):
    uid = request.session.get('login')
    if Roadshow.objects.filter(~Q(valid=True), user__pk=uid).exists(): return Response({'status':1, 'msg':'您还有路演申请仍在审核中'})
    user = User.objects.get(pk=uid)
    name = request.data.get('name', '').strip()
    company = request.data.get('company', '').strip()
    if not name or not company: return myarg('name or company')
    telephone = request.data.get('telephone', '').strip()
    if validate_telephone(telephone) == False: return Response({'status':1, 'msg':'手机格式不正确'})
    vcr = request.data.get('vcr')
    print(vcr)
    obj = Roadshow.objects.create(
        user=user, 
        comment=company, 
        contact_name=name, 
        contact_phone=telephone,
        vcr = vcr,
    )
    return Response({'status':0, 'msg':'上传项目成功, 您的项目已成功入选项目库', 'data':obj.id})

@api_view(['POST', 'GET'])
@islogin()
def activity(request):
    if not Activity.objects.all().exists(): return Response({'status':-1, 'msg':'目前没有活动'})
    ac = Activity.objects.all()[0]
    if timezone.now() > ac.stop_datetime: return Response({'status':-1, 'msg':'目前没有活动'})
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
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
@islogin()
def signin(request, pk):
    item = getinstance(Activity, pk)
    if not item: return NOENTITY
    user = User.objects.get(pk=request.session.get('login'))
    if Signin.objects.filter(user=user, activity=item).exists(): return Response({'status':0, 'msg':'你已签到, 无需重复签到'})
    if timezone.now() > item.stop_datetime: return Response({'status':1, 'msg':'对不起, 此活动已结束'})
    Signin.objects.create(user=user, activity=item)
    return Response({'status':0, 'msg':'恭喜您, 签到成功!'})

#@api_view(['POST'])
#@islogin()
#def addcompany(request):
#    uid = request.session.get('login')
#    user = User.objects.get(pk=uid)
#    invalids = JoinShip.objects.filter(~Q(valid=True), user=user)
#    if invalids.exists(): return Response({'status':1, 'msg':'您尚有公司在审核中, 请耐心等待'})
#    name = request.data.get('company_name')
#    company = Company.objects.filter(name=name)
#    if company.exists(): company = company[0]
#    else:
#        province = request.data.get('province')
#        city = request.data.get('city')
#        industry= request.data.get('industry_type').split(',')
#        companystatus = request.data.get('company_status')
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
#    return Response({'status':0, 'msg':'公司添加成功', 'data':data})

@api_view(['POST'])
@islogin()
def editcompany(request, pk):
    return Response({'status':0, 'msg':''})

#@api_view(['POST', 'GET'])
#def companyinfo(request, pk):
#    item = getinstance(Company, pk)
#    if not item: return NOENTITY
#    data = dict()
#    data['industry_type'] = [it.name for it in item.industry.all()]
#    data['province'] = item.province
#    data['city'] = item.city
#    data['company_status'] = item.companystatus.name
#    return Response({'status':0, 'msg':'', 'data':data})

#@api_view(['POST', 'GET'])
#@islogin()
#def companylist(request):
#    user = User.objects.get(pk=request.session.get('login'))
#    data = [{'id':o.id, 'company_name':o.name} for o in user.company.all()]
#    return Response({'status':0, 'msg':'', 'data':data})

#@api_view(['POST', 'GET'])
#def industry(request):
#    data = [{'id':o.id, 'type_name':o.name} for o in Industry.objects.all()]
#    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def companystatus(request):
    data = [{'id':o.id, 'status_name':o.name} for o in Companystatus.objects.all()]
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def investorqualification(request):
    data = [{'id':o.id, 'desc':o.desc} for o in Qualification.objects.all()]
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def fundsizerange(request):
    data = [{'id':o.id, 'desc':o.desc} for o in FundSizeRange.objects.all()]
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
@islogin()
def authenticate(request):
    name = request.data.get('name','').strip()
    position = request.data.get('position', '').strip()
    company = request.data.get('company','').strip()
    if not name or not position or not company: return myarg('请完善信息')
    qualification = request.data.get('qualification','').strip()
    if not MTM_RE.match(qualification): return myarg('qualification')

    user = User.objects.get(pk=request.session.get('login'))
    queryset = Investor.objects.filter(user=user)

    if queryset.exists():
        valid = queryset[0].valid
        if valid == None: return Response({'status':1, 'msg':'该身份认证正在审核中'})
        elif valid == False: return Response({'status':1, 'msg':'认证失败, 请去用户中心查看详情'})
        else: return Response({'status':1, 'msg':'认证成功'})
    
    investor = Investor.objects.create(
         user=user,
         position = position,
         comment = company
    )
    investor.qualification = qualification.split(',')
    user.name = name; user.save()
    return Response({'status':0, 'msg':'提交成功, 等待审核'})

@api_view(['POST', 'GET'])
@islogin()
def businesscard(request, pk):
    investor = Investor.objects.get(pk=pk)
    mystorage_file(
        investor.card,
        request.data.get('file'),
        'investor/%Y/%m'
    )
    return Response({'status':0, 'msg':'名片上传成功'})

@api_view(['POST'])
@islogin()
def idfore(request):
    img = request.data.get('file')
    user = User.objects.get(pk=request.session.get('login'))
    mystorage_file(user.idfore, img)
    return Response({'status':0, 'msg':'身份证上传成功'})

@api_view(['POST', 'GET'])
@islogin()
def userimg(request):
    user = User.objects.get(pk=request.session.get('login'))
    if request.method == 'POST':
        img = request.data.get('file')
        mystorage_file(user.img, img)
        return Response({'status':0, 'msg':'图像设置成功'})
    elif request.method == 'GET':
        data = dict()
        data['img']= myimg(user.img) 
        data['name'] = user.name
        return Response({'status':0, 'msg':'', 'data':data})

@api_view(['GET','POST'])
def position(request):
    data = [{'id':o.id, 'type_name':o.name} for o in Position.objects.all()]
    return Response({'status':0, 'msg':'', 'data':data})

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
    if not MTM_RE.match(position): return myarg('position')
    user = User.objects.get(pk=request.session.get('login'))
    user.position = position.split(',')
    return Response({'status':0, 'msg':'职位设置成功'})

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
    return  g_project(queryset, page)

@api_view(['GET', 'POST'])
@islogin()
def collectfinanced(request, page):
    uid = request.session.get('login')
    now = timezone.now()
    queryset = CollectShip.objects.filter(
        user__pk=uid,
        project__finance_stop_datetime__lt=now
    )
    return g_project(queryset, page)

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
    return g_project(queryset, page)

@api_view(['POST', 'GET'])
@islogin()
def feedback(request):
    uid = request.session.get('login')
    advice = request.data.get('advice', '').strip()
    if not advice: return ARG
    #if Feedback.objects.filter(user__pk=uid, valid=None).exists():
    #    return Response({'status':0, 'msg':''})
    Feedback.objects.create(
        user = User.objects.get(pk=uid),
        advice = advice
    )
    return Response({'status':0, 'msg':'反馈成功'})

@api_view(['GET', 'POST'])
def keyword(request):
    industrys = Industry.objects.filter(~Q(valid=False))
    data = list()
    for keyword in industrys:
        tmp = dict()
        tmp['id'] = keyword.id
        tmp['word'] = keyword.name
        data.append(tmp)
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def projectsearch(request, pk, page):
    if pk == '0': 
        value = request.data.get('value').strip()
        if not value: return myarg('value')
        queryset = Project.objects.filter(company__name__contains=value)
    else: queryset = Project.objects.filter(company__industry__in=[int(pk),])
    return g_project(queryset, page)

@api_view(['GET', 'POST'])
@islogin()
def generalinformation(request, pk=None):
    if pk: uid = pk
    else: uid = request.session.get('login')
    data = dict()
    data['uid'] = uid
    data['telephone'] = User.objects.get(pk=uid).telephone
    user = User.objects.get(pk=uid)
    data['user_img'] = myimg(user.img)
    data['real_name'] = user.name
    data['gender'] = user.gender
    data['position_type'] = [pt.name for pt in user.position.all()]
    data['province'] = user.province
    data['city'] = user.city
    return Response({'status':0, 'msg':'', 'data':data})

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
    return Response({'status':0, 'msg':'', 'data':data})
        
@api_view(['GET', 'POST'])
@islogin()
def wantinvest(request, pk):
    flag = request.data.get('flag','').strip()
    if not re.match('^[01]$', flag): return ARG
    invest_amount = request.data.get('invest_amount', '').strip() # 投资金额
    if not PK_RE.match(invest_amount): return ARG
    investor = request.data.get('investor', '').strip() # 投资人id
    if not PK_RE.match(investor): 
        return  Response({'status':1, 'msg':'请选择您的投资人身份'})
    project = getinstance(Project, pk) # 项目
    if not project: return NOENTITY
    fund = project.leadfund if flag=='1' else project.followfund
    if int(invest_amount) < fund:
        return Response({'status':1, 'msg':'金额必须大于%s' % fund})
    uid = request.session.get('login')
    investor_obj = Investor.objects.filter(pk=investor, user__pk=uid) # 投资人实体
    if not investor_obj.exists():
        return Response({'status':-9, 'msg':'该投资人不存在'})
    investship = InvestShip.objects.filter(project__pk=pk, investor__pk=investor) #是否投资过
    if investship.exists():
        return Response({'status':1, 'msg':'您已投资过该项目, 请到用户中心查看'})
    InvestShip.objects.create(
        investor = investor_obj[0],
        project = project,
        invest_amount = invest_amount,
        lead = int(flag)
    )
    return Response({'status':0, 'msg':'工信您, 投资信息提交成功'})

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
            tmp['reject_reason'] = '等待审核, 预计2天内处理完毕'
        data.append(tmp)
    return Response({'status':0, 'msg':'', 'data':data})

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
            tmp['reason'] = '等待审核, 预计2天内处理完毕' 
        data.append(tmp)
    return Response({'status':0, 'msg':'', 'data':data})

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
            tmp['reason'] = '等待审核, 预计2天内处理完毕'
        data.append(tmp)
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['GET', 'POST'])
@islogin()
def mycreateproject(request, page):
    uid = request.session.get('login')
    ret = g_project( Project.objects.filter(roadshow__user__isnull=False, roadshow__user__pk=uid), page )
    return ret

@api_view(['GET', 'POST'])
@islogin()
def myinvestproject(request, page):
    uid = request.session.get('login')
    ret = g_project( InvestShip.objects.filter(investor__user__pk=uid), page )
    return ret

@api_view(['POST'])
@islogin()
def token(request):
    uid = request.session.get('uid')
    if Roadshow.objects.filter(~Q(valid=True), user__pk=uid).exists(): return Response({'status':1, 'msg':'您还有路演申请仍在审核中'})
    key = request.data.get('key', '').strip()
    print(key)
    if not key: return myarg('key')
    q = Auth(settings.AK, settings.SK)
    token = q.upload_token(settings.BN, key)
    token2 = q.upload_token(settings.BN, key, 7200, {'callbackUrl':'http://115.28.177.22:8000/phone/callback/', 
        'callbackBody':'name=$(fname)&hash=$(etag)'})
    print(token2)
    return Response({'status':0, 'msg':'', 'data':token2})

def createurl(name):
    if not name: return ''
    q = Auth(settings.AK, settings.SK)
    url = 'http://%s/%s' % (settings.BD, name)
    url = q.private_download_url(url, expires=3600)
    print(url)
    return url

@api_view(['POST', 'GET'])
def callback(request):
    name = request.data.get('name', '').strip()
    if not name: return myarg('name')
    url = createurl(name)
    return Response({'status':0, 'msg':'视频上传成功', 'data':url})

@api_view(['POST', 'GET'])
def qiniudelete(request):
    key = ''
    q = Auth(settings.AK, settings.SK)
    bucket = BucketManager(q)
    ret, info = bucket.delete(settings.BN, key)
    print(info)
    assert ret is None
    assert info.status_code == 612
    
@api_view(['POST'])
@islogin()
def deletevideo(request):
    key = request.data.get('key','').strip()
    if not key: return Response({'status':1, 'msg':'参数错误'})
    q = Auth(settings.AK, settings.SK)
    bucket = BucketManager(q)
    ret, info = bucket.delete(settings.BN, key)
    assert ret is None
    assert info.status_code == 612
    return Response({'status':0, 'msg':'删除视频成功'})

@api_view(['POST', 'GET'])
@islogin()
def ismyproject(request, pk):
    project = getinstance(Project, pk)
    if not project: return NOENTITY
    uid = request.session.get('login')
    if project.roadshow and  project.roadshow.user.id == uid: 
        return Response({'status':1, 'msg':'你不可以给自己的项目投资哦'})
    return Response({'status':0, 'msg':''})

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
        return Response({'status':1, 'msg':'您的认证尚在审核中'})
    else:
        return Response({'status':1, 'msg':'对不起, 您的认证失败'})

@api_view(['POST', 'GET'])
@islogin()
def investorinfo(request, pk):
    investor = getinstance(Investor, pk)
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
        data['telephone'] = investor.user.telephone
        data['province'] = user.province
        data['city'] = user.city
        data['company'] = investor.comment
        data['position'] = investor.position
    return Response({'status':0, 'msg':'', 'data':data})

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
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def checkupdate(request, system):
    return Response({'status':1, 'msg':'没有更新'})
    queryset = Version.objects.filter(system__id=system)
    if not queryset: 
        return Response({'status':0, 'msg':''})
    version = queryset[0] 
    data = dict()
    data['force'] = True #False
    data['edition'] = version.edition
    data['item'] = version.item
    data['href'] = version.href 
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def shareproject(request, pk):
    data = dict()
    data['title'] = '项目分享'
    data['img'] = '%s/static/app/img/icon.png' % settings.RES_URL
    data['url'] = 'http://a.app.qq.com/o/simple.jsp?pkgname=com.jinzht.pro'
    data['content'] = '项目分享'
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def shareapp(request):
    data = dict()
    data['title'] = 'app分享'
    data['img'] = '%s/static/app/img/icon.png' % settings.RES_URL
    data['url'] = 'http://a.app.qq.com/o/simple.jsp?pkgname=com.jinzht.pro'
    data['content'] = '金指投App分享'
    return Response({'status':0, 'msg':'', 'data':data})

def document(name):
    cur_dir = os.path.dirname(__file__)
    f = os.path.join(cur_dir, 'document/%s' %name )
    if not os.path.exists(f):
        return Response({'status':1, 'msg':'数据加载有误', 'data':'no data'})

    import codecs
    with codecs.open(f, 'r', 'utf-8') as fp:
        data = fp.read()
        return Response({'status':0, 'msg':'', 'data':data})

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
    project = getinstance(Project, pk)
    if not project: return NOENTITY
    at_topic = request.data.get('at_topic',0)
    if not at_topic: 
        at_topic = None
        msg = '发表话题成功'
    else: 
        at_topic = getinstance(Topic, at_topic)
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
    queryset = g_queryset(queryset, page)
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
    status = -int(len(queryset)<6)
    return Response({'status':status, 'msg':'加载完毕', 'data':data})

@api_view(['POST', 'GET'])
@islogin()
def topiclist(request, pk, page):
    queryset = Topic.objects.filter(project__pk=pk)
    ret = g_topiclist(queryset, page)
    return ret
   
def g_news(queryset, page):
    queryset = g_queryset(queryset, page)
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
    status = -int(len(queryset)<PAGE_SIZE)
    return Response({'status': status, 'msg':'加载完毕', 'data':data})

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
    news = getinstance(News, pk) 
    if not news: return NOENTITY 
    data = dict()
    data['href'] = '%s/%s/%s' %(settings.RES_URL, settings.NEWS_URL_PATH, news.name)
    data['src'] = news.src 
    data['title'] = news.title
    data['content'] = news.content
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
def newssharecount(request, pk):
    news = getinstance(News, pk) 
    if not news: return NOENTITY 
    news.sharecount += 1
    news.save()
    return Response({'status':0, 'msg':''})
        
@api_view(['POST', 'GET'])
def newsreadcount(request, pk):
    news = getinstance(News, pk) 
    if not news: return NOENTITY 
    news.readcount += 1
    news.save()
    return Response({'status':0, 'msg':''})
    
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
    return Response({'status':0, 'msg':'', 'data':data})

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
    return Response({'status':0, 'msg':'', 'data':data})    

@api_view(['POST', 'GET'])
@islogin()
def systeminform(request, page):
    uid = request.session.get('login')
    queryset = SystemInform.objects.filter(user__pk=uid)
    queryset = g_queryset(queryset, page)
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
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
@islogin()
def setsysteminform(request, pk):
    systeminform = getinstance(SystemInform, pk)
    if not systeminform: return myarg('systeminform')
    systeminform.read = True
    systeminform.save()
    return Response({'status':0, 'msg':'', 'data':systeminform.read})

@api_view(['POST', 'GET'])
@islogin()
def deletesysteminform(request, pk):
    systeminform = getinstance(SystemInform, pk)
    if not systeminform: return myarg('systeminform')
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    if systeminform.user == user:
        systeminform.delete()
        return Response({'status':0, 'msg':'删除成功'})
    return Response({'status': 1, 'msg':'不能删除别人的消息'})

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
        return Response({'status':0, 'msg':'全部设为已读成功'})
    topic = getinstance(Topic, pk)
    if not topic: return NOENTITY
    topic.read = None 
    topic.save()
    return Response({'status':0, 'msg':'删除成功'})

@api_view(['POST', 'GET'])
def latestnewscount(request):
    yesterday = timezone.now() - timedelta(days=1)
    queryset = News.objects.filter(~Q(newstype=4), create_datetime__gt=yesterday)
    return Response({'status':0, 'msg':'', 'data':{'count':queryset.count()}})
    
@api_view(['POST', 'GET'])
def latestknowledgecount(request):
    yesterday = timezone.now() - timedelta(days=1)
    queryset = News.objects.filter(newstype=4, create_datetime__gt=yesterday)
    return Response({'status':0, 'msg':'', 'data':{'count':queryset.count()}})

def g_feelinglikers(queryset, page, pagesize=settings.FEELINGLIKERS_INITAL_PAGESIZE): 
    queryset = g_queryset(queryset, page, pagesize)
    data = list()
    for item in queryset:
        tmp = dict()
        tmp['name'] = item.name
        tmp['uid'] = item.id
        tmp['photo'] = myimg(item.img)
        data.append(tmp)
    return data

def __feelingcomment(item, user):
    tmp = dict()
    tmp['id'] = item.id
    tmp['flag'] = item.user == user
    tmp['name'] = '%s' % (item.user.name)
    tmp['uid'] = item.user.id
    tmp['photo'] = myimg(item.user.img)
    if item.at:
        tmp['at_label'] = settings.AT_LABEL
        tmp['at_uid'] = item.at.user.id
        tmp['at_name'] = item.at.user.name
    tmp['label_suffix'] = settings.LABEL_SUFFIX
    tmp['content'] = '%s' % (item.content)
    return tmp

def g_feelingcomment(queryset, user, page):
    queryset = g_queryset(queryset, page, settings.FEELINGCOMMENT_PAGESIZE)
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
    tmp['datetime'] = datetime_filter(item.create_datetime)
    tmp['name'] = item.user.name
    tmp['photo'] = myimg(item.user.img)
    tmp['content'] = item.content
    tmp['pics'] = [] if item.pics==''  else [ os.path.join(settings.RES_URL, v) for v in item.pics.split(';') ]
    tmp['is_like'] = user in item.likers.all()
    tmp['likers'] = g_feelinglikers(item.likers.all(), 0) # page_size=3
    remain_likers_num = item.likers.all().count() - 3
    tmp['remain_likers_num'] = 0 if remain_likers_num <=0 else remain_likers_num
    tmp['position'] = [ v.name for v in item.user.position.all() ]
    tmp['city'] = item.user.city 
    queryset = Feelingcomment.objects.filter(feeling=item, valid=None)
    data = g_feelingcomment(queryset, user, 0)
    tmp['comment'] = data
    remain_comment_num = queryset.count() - 15
    tmp['remain_comment_num'] = 0 if remain_comment_num <=0 else remain_comment_num 
    return tmp  

@api_view(['GET'])
@islogin()
def getfeeling(request, pk):
    item = getinstance(Feeling, pk)
    if not item: return NOENTITY
    user = User.objects.get(pk = request.session.get('login'))
    data = __feeling(item, user) 
    return Response({'status':0, 'msg':'', 'data':data})

@api_view(['POST', 'GET'])
@islogin()
def feeling(request, page):
    user = User.objects.get(pk = request.session.get('login'))
    pagesize = settings.FEELING_PAGESIZE
    queryset = g_queryset(Feeling.objects.all(), page, pagesize) 
    data = list()
    for item in queryset: data.append( __feeling(item, user) )
    status = -(len(data) < pagesize)
    return Response({'status':status, 'msg':'', 'data':data})

@api_view(['POST'])
@islogin()
def postfeeling(request):
    content = request.data.get('content', '').rstrip()
    relative_path = datetime.now().strftime('media/feeling/%Y/%m')
    absolute_path = os.path.join(settings.BASE_DIR, relative_path)   
    if request.FILES: mkdirp(absolute_path)
    elif not content: return Response({'status':1, 'msg':'发表内容不能为空'})
    relative_path_list = list()
    for k, v in request.FILES.items():
        ext = imghdr.what(v)
        if ext not in settings.ALLOW_IMG: return Response({'status':1, 'msg':'图片格式不正确'})
        img_name = '{}.{}'.format(uuid.uuid4().hex, ext)
        img = os.path.join(absolute_path, img_name)
        with open(img, 'wb') as fp:
            for data in v.chunks(): fp.write(data)
        relative_path_list.append( os.path.join(relative_path, img_name) )
    uid = request.session.get('login')
    user = User.objects.get(pk=uid)
    obj = Feeling.objects.create(
        user = user,
        content = content,
        pics = ';'.join(relative_path_list),
    )
    data = __feeling(obj, user) 
    return Response({'status':0, 'msg':'发表成功', 'data':data})

@api_view(['POST'])
@islogin()
def deletefeeling(request, pk):
    item = getinstance(Feeling, pk)
    if not item: return NOENTITY
    user = User.objects.get(pk=request.session.get('login'))
    if item.user == user:
        item.delete()
        return Response({'status':0, 'msg':'删除状态成功'})
    return Response({'status':1, 'msg':'不能删除别人的状态'})

@api_view(['POST'])
@islogin()
def likefeeling(request, pk, is_like):
    item = getinstance(Feeling, pk)
    if not item: return NOENTITY
    user = User.objects.get(pk=request.session.get('login'))
    data = dict()
    data['is_like'] = not int(is_like)
    data['name'] = user.name
    data['uid'] = user.id
    data['photo'] = myimg(user.img)
    if is_like == '0': 
        item.likers.add(user)
        return Response({'status':0, 'msg':'点赞成功', 'data':data})
    else: 
        item.likers.remove(user)
        return Response({'status':0, 'msg':'取消点赞', 'data':data})

@api_view(['GET'])
@islogin()
def feelinglikers(request, pk, page):
    item = getinstance(Feeling, pk)
    if not item: return NOENTITY
    queryset = item.likers.all()
    pagesize = settings.FEELINGLIKERS_PAGESIZE
    data = g_feelinglikers(queryset, page, pagesize)
    status = -(len(data)<pagesize)
    return Response({'status':status, 'msg':'', 'data':data})

@api_view(['GET'])
@islogin()
def feelingcomment(request, pk, page):
    item = getinstance(Feeling, pk)
    if not item: return NOENTITY
    user = User.objects.get(pk=request.session.get('login'))
    queryset = Feelingcomment.objects.filter(feeling=item, valid=None)
    pagesize = settings.FEELINGCOMMENT_PAGESIZE
    data = g_feelingcomment(queryset, user, page)
    status = -(len(data)<pagesize)
    return Response({'status':status, 'msg':'', 'data':data})

@api_view(['POST'])
@islogin()
def postfeelingcomment(request, pk):
    item = getinstance(Feeling, pk)
    content = request.data.get('content', '').rstrip()
    at = atid = request.data.get('at', None)
    if not item: return NOENTITY
    if not content: return Response({'status':1, 'msg':'回复内容不能为空'})
    user = User.objects.get(pk = request.session.get('login'))
    if at:
        at = getinstance(Feelingcomment, at)
        if at and user == at.user: return Response({'status':1, 'msg':'不能给自己回复哦'})
    obj = Feelingcomment.objects.create(
        feeling = item,
        user = user,
        content = content,
        at = at,
    )
    data = __feelingcomment(obj, user)
    return Response({'status':0, 'msg':'回复成功', 'data':data})

@api_view(['POST'])
@islogin()
def hidefeelingcomment(request, pk):
    item = getinstance(Feelingcomment, pk)
    if not item: return NOENTITY
    user = User.objects.get(pk=request.session.get('login'))
    if item.user == user:
        item.valid = False; item.save()
        return Response({'status':0, 'msg':'删除评论成功'})
    return Response({'status':0, 'msg':'不能删除别人的评论'})

@api_view(['POST', 'GET'])
@islogin()
def feelingbackground(request):
    user = User.objects.get(pk=request.session.get('login'))
    if request.method == 'GET':
        data = dict()
        data['background'] = myimg(user.background) 
        data['photo'] = myimg(user.img)
        return Response({'status': 0, 'msg': '', 'data': data})
    elif request.method == 'POST':
        img = request.data.get('file')
        ext = imghdr.what(img)
        if ext not in settings.ALLOW_IMG: return Response({'status':1, 'msg':'图片格式不正确'})
        mystorage_file(user.background, img) 
        return Response({'status': 0, 'msg': '背景设置成功'})
