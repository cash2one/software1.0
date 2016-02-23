# coding: utf-8
from django.db import models
from django.db.models import *
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.core.files.storage import FileSystemStorage
from django.db import IntegrityError, transaction

from utils.utils import *
from jinzht.config import *

class MyFileStorage(FileSystemStorage):
    def get_available_name(self, name):
        return name

def osremove(old, new):
    if old and old != new:
        os.path.exists(old.path) and os.remove(old.path)

@deconstructible
class UploadTo(object):
    path = "{0}/{1}"

    def __init__(self, sub_path):
        self.sub_path = datetime.now().strftime(sub_path)

    def __call__(self, instance, filename):
        ext = os.path.splitext(filename)[-1]
        filename = '{}{}'.format(uuid.uuid4().hex, ext)
        return '{}/{}'.format(self.sub_path, filename)


class Institute(Model):

    name = CharField('机构名称', max_length=64, unique=True)
    addr = CharField('地址', max_length=128, blank=True)
    foundingtime = DateField('成立时间', blank=True)
    fundsize = CharField('基金规模', max_length=64, blank=True)
    profile = TextField('机构介绍', blank=True)
    logo = ImageField('logo', upload_to=UploadTo('institute/orgcode/%Y/%m'), blank=True)
    investcase = ManyToManyField('InvestCase', related_name='investcase', verbose_name='投资案例', blank=True)
    homepage = URLField('网站主页', max_length=64, blank=True)
    create_datetime = DateTimeField('添加时间', auto_now_add=True)

    def __str__(self): return '%s' % self.name

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '机构'

    def save(self, *args, **kwargs):
        edit = self.pk
        if edit: item = Institute.objects.get(pk=self.pk)
        super(Institute, self).save(*args, **kwargs)
        if edit:
            osremove(item.logo, self.logo)

class InvestCase(Model):
    company = CharField('公司名称', max_length=64)
    logo = ImageField('公司logo', upload_to=UploadTo('investcase/logo/%Y/%m'), blank=True)

    def __str__(self):
        return '%s' % (self.company)

    class Meta:
        ordering = ('pk',)
        verbose_name = verbose_name_plural = '机构投资案例' 

    def save(self, *args, **kwargs):
        edit = self.pk
        if edit:
            investcase = InvestCase.objects.get(pk=self.pk)
            osremove(investcase.logo, self.logo)
        super(InvestCase, self).save(*args, **kwargs)

class User(Model):
   
    ''' 微信授权登录 '''
    openid = CharField('微信', max_length=64, blank=True) # 微信授权登录的返回序列号
    photo = ImageField('图像', upload_to=UploadTo('user/photo/%Y/%m'), blank=True) # 微信的图像, 用户可以自己设置, 默认为微信没有的图像
    nickname = CharField('昵称', max_length=256, blank=True) # 微信的昵称, 用户可以自己设置, 默认为匿名用户 
    bg = ImageField('微信背景', upload_to=UploadTo('user/bg/%Y/%m/'), blank=True)

    ''' 手机登录 '''
    tel = CharField('手机', max_length=11, unique=True, blank=True, validators=[valtel])
    passwd = CharField('密码', max_length=32, blank=True)

    ''' 系统, 极光, 版本 '''
    os = PositiveIntegerField('操作系统', choices=OS) # 系统类别
    regid = CharField('唯一识别码', max_length=32, blank=True) # 极光推送
    version = CharField('版本', max_length=64, blank=True) # 版本号, 用户更新检测
    create_datetime = DateTimeField('注册时间', auto_now_add=True)
    lastlogin = DateTimeField('上次登录时间', null=True, blank=True)

    ''' 必填信息 '''
    name = CharField('姓名', max_length=16, blank=True) # 真实姓名 cation
    idno = CharField('身份证号码', max_length=18, blank=True) # 身份证号码 cation 
    
    ''' 可选信息 '''
    email = EmailField('邮件地址', max_length=64, blank=True) # 邮件地址
    company = CharField('公司', max_length=64, blank=True) # cation
    position= CharField('职位', max_length=64, blank=True) # cation
    addr = CharField('地址', max_length=64, blank=True)

    ''' 自动维护 '''
    gender = NullBooleanField('性别("男")', default=None)
    birthplace = CharField('出生地', max_length=128, blank=True)
    birthday = DateField('生日', null=True, blank=True)

    ''' 认证信息 '''
    idpic = ImageField('身份证', upload_to=UploadTo('company/idpic/%Y/%m'), blank=True)
    qualification = CharField('认证条件', max_length=32, blank=True)
    comment = CharField('备注', max_length=64, blank=True)

    ''' 信息是否属实 '''
    valid = NullBooleanField('是否属实')

    ''' 投资人详情  '''
    img = ImageField('投资人图像', upload_to=UploadTo('user/img/%Y/%m'), blank=True)
    signature = CharField('签名', max_length=64, blank=True)
    investplan = TextField('投资规划', max_length=256, blank=True)
    investcase = TextField('投资案例', max_length=256, blank=True)
    profile = TextField('个人介绍', max_length=256, blank=True)

    def save(self, *args, **kwargs): #密码的问题
        edit = self.pk
        if edit: 
            user = User.objects.get(pk=self.pk)
            if user.qualification != self.qualification:
                MAIL('认证', '%s 在 %s 申请认证' % (self.tel, timeformat()) ).send()
            if user.valid != self.valid:
                if self.valid == True:
                    SMS(self.tel, AUTH_TRUE).send()
                elif self.valid == False:
                    SMS(self.tel, AUTH_FALSE).send()
            osremove(user.photo, self.photo)
            osremove(user.bg, self.bg)
            osremove(user.idpic, self.idpic)
            osremove(user.img, self.img)
        else:
            SMS(self.tel, REGISTE).send()
            MAIL('用户注册', '%s 在 %s 注册' % (self.tel, timeformat()) ).send()
        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return '%s:%s' % (self.name, self.tel)

    class Meta:
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '注册用户'


class Company(Model):

    name = CharField('公司名称', max_length=64, unique=True)
    abbrevname = CharField('公司简称', max_length=64, blank=True)
    addr = CharField('地址', max_length=128)
    logo = ImageField('公司图片', upload_to=UploadTo('company/logo/%Y/%m'), blank=True)
    profile = TextField('公司介绍', blank=True)
    license = ImageField('营业执照', upload_to=UploadTo('company/license/%Y/%m'), blank=True)
    orgcode = ImageField('组织机构代码证', upload_to=UploadTo('company/orgcode/%Y/%m'), blank=True)
    homepage = URLField('网站主页', max_length=64, blank=True)
    create_datetime = DateTimeField('添加时间', auto_now_add=True)

    def save(self, *args, **kwargs):
        edit = self.pk
        if edit: company = Company.objects.get(pk=self.pk)
        super(Company, self).save(*args, **kwargs)
        if edit:
            osremove(company.logo, self.logo)
            osremove(company.license, self.license)
            osremove(company.orgcode,self.orgcode)

    def __str__(self): return '%s' % self.name

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '公司'


class Upload(Model):        

    ''' 上传的项目 '''
    user = ForeignKey('User', verbose_name='上传人')
    company = CharField('公司名称', max_length=64)
    img = ImageField('项目图片', upload_to=UploadTo('upload/img/%Y/%m'), blank=True) 
    planfinance = PositiveIntegerField('计划融资', blank=True, null=True)
    profile = TextField('公司简介', blank=True)
    business = TextField('主营业务', blank=True)
    model = TextField('商业模式', blank=True)
    desc = TextField('项目描述')
    vcr = CharField('vcr', max_length=64, blank=True)
    like = ManyToManyField('User', related_name='upload_like', verbose_name='点赞', blank=True)
    collect = ManyToManyField('User', related_name='upload_attend', verbose_name='收藏', blank=True)
    create_datetime = DateTimeField('添加时间', auto_now_add=True)
    valid = NullBooleanField('是否合法')
    num = PositiveSmallIntegerField('剩余修改次数', default=5)

    def __str__(self): return '%s' % self.company

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '上传项目'

    def save(self, *args, **kwargs):
        edit = self.pk
        if edit: upload = Upload.objects.get(pk=self.pk)
        super(Upload, self).save(*args, **kwargs)
        if edit:
            osremove(upload.img, self.img)


class Project(Model):

    upload = ForeignKey('Upload', verbose_name='上传项目', null=True, blank=True) # 关联项目

    ''' 项目所关联的公司 '''
    company = ForeignKey('Company', verbose_name='公司', on_delete=PROTECT, blank=True)
    video = URLField('视频地址', blank=True)
    tag = CharField('标签', max_length=32)
   
    ''' 项目概况 '''
    img = ImageField('图片', upload_to=UploadTo('project/img/%Y/%m')) 
    model = TextField('商业模式', blank=True)
    business = TextField('主营业务', blank=True)

    ''' 具体情况 '''
    planfinance = PositiveIntegerField('计划融资')
    finance2get = PositiveIntegerField('已获得融资')
    share2give = DecimalField('让出股份', max_digits=4, decimal_places=2)
    quitway = CharField('退出方式', max_length=32)
    usage = TextField('资金用途')
    invest2plan = PositiveIntegerField('股东人数')
    minfund = PositiveIntegerField('投资最低额度')
   
    ''' 时间 '''
    start = DateTimeField('融资时间', null=True, blank=True)
    stop = DateTimeField('融资结束', null=True, blank=True)
    over = NullBooleanField('众筹完成')
    create_datetime = DateTimeField('创建时间', auto_now_add=True)

    ''' 人数情况 '''
    attend = ManyToManyField('User', related_name='project_attend', verbose_name='与会者', blank=True)
    like = ManyToManyField('User', related_name='project_like', verbose_name='点赞', blank=True)
    collect = ManyToManyField('User', related_name='project_collect', verbose_name='收藏', blank=True)

    ''' 公司新闻 '''
    event = TextField('公司新闻', blank=True)

    rcmd = NullBooleanField('推荐')

    def __str__(self): return '%s%s' % (self.pk, self.company)
    
    class Meta:
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '项目具体信息'

    def save(self, *args, **kwargs):
        edit = self.pk
        if edit: project = Project.objects.get(pk=self.pk)
        super(Project, self).save(*args, **kwargs)
        if edit: osremove(project.img ,self.img)


class Member(Model):

    project = ForeignKey(Project, verbose_name='项目')  
    name = CharField('姓名', max_length=32)
    photo = ImageField('头像', upload_to=UploadTo('member/photo/%Y/%m'), blank=True)
    position = CharField('职位', max_length=32)
    profile = TextField('简介')
    create_datetime = DateTimeField('创建时间', auto_now_add=True)

    def __str__(self): return '%s' % self.project

    class Meta:
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '核心成员'

    def save(self, *args, **kwargs):
        edit = self.pk
        if edit: member = Member.objects.get(pk=self.pk)
        super(Member, self).save(*args, **kwargs)
        if edit: osremove(member.photo, self.photo)


class Invest(Model):

    project = ForeignKey('Project', verbose_name='项目方', on_delete=PROTECT)
    user = ForeignKey('User', verbose_name='投资人', on_delete=PROTECT)
    amount = PositiveIntegerField('投资金额')
    lead = NullBooleanField('领投')
    valid = NullBooleanField('是否合法')
    create_datetime = DateTimeField('投资日期', auto_now_add=True)

    def __str__(self): return '%s/%s/%s' % (self.project, self.user, self.amount)
    
    class Meta:
        unique_together = ('project', 'user')
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '$$$投资关系$$$'
    
    def save(self, *args, **kwargs):
        edit = self.pk
        super(Invest, self).save(*args, **kwargs)
        if edit: pass
        else:
            tp = self.user.tel 
            ri = self.user.regid
            dt = timeformat(self.create_datetime)
            pj = self.project.company.name
            am = self.amount
            text = INVEST_VALID_TRUE %(dt, pj, am)
            JG(text).single(ri) 
            SMS(tp, text).send()
            MAIL( '投资申请', '%s于%s投资"%s"%s万' %(tp, dt, pj, am) ).send()

class Banner(Model):

    title = CharField('题目', max_length=16)
    project = OneToOneField('Project', verbose_name='项目', blank=True, null=True)
    img = ImageField('图片', upload_to=UploadTo('banner/img/%Y/%m'))
    url = URLField('链接地址', max_length=64, blank=True)
    create_datetime = DateTimeField('创建日期', auto_now=True)

    def __str__(self): return '%s' % self.title

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '旗标栏'

    def save(self, *args, **kwargs):
        edit = self.pk
        if edit: banner = Banner.objects.get(pk=self.pk)
        super(Banner, self).save(*args, **kwargs)
        if edit: osremove(banner.img, self.img) 


class Thinktank(Model):

    name = CharField('姓名', max_length=16)
    signature = CharField('签名', max_length=64)
    company = CharField('公司', max_length=64)
    position = CharField('职位', max_length=64)
    photo = ImageField('图像', upload_to=UploadTo('thinktank/photo/%Y/%m'))
    video = URLField('链接地址', max_length=64, blank=True)
    experience = TextField('经历')
    case = TextField('成功案例')
    domain = TextField('擅长领域')
    create_datetime = DateTimeField('创建日期', auto_now_add=True)

    def __str__(self):
        return '%s' % self.name

    class Meta:
        ordering = ('pk',)
        verbose_name = verbose_name_plural = '智囊团'

    def save(self, *args, **kwargs):
        edit = self.pk
        if edit: thinktank = Thinktank.objects.get(pk=self.pk)
        super(Thinktank, self).save(*args, **kwargs)
        if edit:
            osremove(thinktank.photo, self.photo)

class NewsType(Model):

    name = CharField('资讯类型名', max_length=16, unique=True)
    valid = NullBooleanField('是否真实', default=None)
    eng = CharField('对应英文', max_length=64)

    def __str__(self): return '%s' % self.name

    class Meta:
        ordering = ('pk', )
        verbose_name = verbose_name_plural = '资讯类型'
    
class News(Model):

    newstype = ForeignKey('NewsType', verbose_name='资讯类型', blank=True, null=True)
    title = CharField('标题', max_length=64)
    img = URLField('图片url', blank=True)
    name = CharField('网页名', max_length=128)
    src = CharField('来源', max_length=64, default='金指投')
    content = TextField('内容', max_length=256)
    share = PositiveIntegerField('分享', default=0)
    read = PositiveIntegerField('阅读数', default=0)
    pub_date = DateField('发布时间', null=True, blank=True)
    create_datetime = DateTimeField('创建时间', auto_now_add=True)
    valid = NullBooleanField('是否合法')

    def __str__(self): return '%s' % self.title

    class Meta:
        ordering = ('-pk', )
        unique_together = ('title', 'pub_date')
        verbose_name = verbose_name_plural = '资讯'

class Topic(Model):
    project = ForeignKey('Project', verbose_name='项目')
    user = ForeignKey('User', verbose_name='发表话题者')
    content = CharField('内容', max_length=128)
    at = ForeignKey('self', verbose_name='@话题', null=True, blank=True)
    valid = NullBooleanField('是否真实', default=None)
    read = NullBooleanField('是否阅读', default=False)
    create_datetime = DateTimeField('创建时间', auto_now_add=True)
   
    def __str__(self): return '%s' % self.content

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '话题'

    def save(self, *args, **kwargs):
        edit = self.pk
        super(Topic, self).save(*args, **kwargs)
        if not edit and self.at:
            JG(
                '%s 回复了你' % self.user.name, 
                {'api': 'msg', 'id': self.project.id},
            ).single(self.at.user.regid)
            

class Push(Model):
    pushtype = PositiveIntegerField('推送类型', choices=PUSHTYPE)
    user = ManyToManyField('User', verbose_name='推送给', blank=True, help_text='如果为空就推送给所有人')
    title = CharField('标题', max_length=32, blank=True)
    content = CharField('内容', max_length=64)
    index = PositiveIntegerField('对应的id', blank=True, null=True)
    url = URLField('地址', blank=True, help_text='如果是网页, 此次段必填')
    valid = NullBooleanField('是否合法', default=None)
    create_datetime = DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return '%s' % (self.pk)

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '推送'

    def save(self, *args, **kwargs):
        edit = self.pk
        super(Push, self).save(*args, **kwargs)
        if self.valid == True:
            extras = {
                'api': PUSHTYPE[self.pushtype-1][1],
                'id': self.index,
                'url': self.url
            }
            if not self.user.count():
                JG(self.content, extras).all()
            else:
                for user in self.user.all(): 
                    user.regid and JG(self.content, extras).single(user.regid)
                    
class Inform(Model):
    user = ForeignKey('User', verbose_name='用户')
    push = ForeignKey('Push', verbose_name='push')
    read = NullBooleanField('是否阅读', default=False)
    create_datetime = DateTimeField('创建时间', auto_now_add=True)


class Feeling(Model):

    user = ForeignKey('User', verbose_name='用户')
    content = TextField('内容', blank=True, null=True)
    pic = TextField('图片地址', blank=True)
    like = ManyToManyField('User', related_name='feeling_like', verbose_name='点赞', blank=True)
    news = ForeignKey('News', verbose_name='资讯', blank=True, null=True, default=None)
    create_datetime = DateTimeField('创建时间', auto_now_add=True)

    def __str__(self): return '%s' % self.id
    
    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '状态发表'

    def delete(self):
        for v in self.pic.split(';'):
            pic = os.path.join(settings.BASE_DIR, v)
            os.path.isfile(pic) and imghdr.what(pic) in settings.ALLOW_IMG and os.remove(pic) 
        return super(Feeling, self).delete()
        

class FeelingComment(Model):

    user = ForeignKey('User', verbose_name='发表话题者')
    feeling = ForeignKey('Feeling', verbose_name='状态')
    content = TextField('内容')
    at = ForeignKey('self', verbose_name='@', null=True, blank=True)
    create_datetime = DateTimeField('创建时间', auto_now_add=True)
    valid = NullBooleanField('是否合法', default=None)

    def __str__(self): return '%s' % self.user

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '话题评论'

    def save(self, *args, **kwargs):
        edit = self.pk
        super(FeelingComment, self).save(*args, **kwargs)
        if not edit:
            if not self.user == self.feeling.user:
                extras = {'api': 'feeling', 'id':self.feeling.id}
                JG('有人提及到您', extras).single(self.feeling.user.regid)
                self.at and self.at.user != self.feeling.user and  JG('有人回复了你', extras).single(self.at.user.regid)
