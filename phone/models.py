# coding: utf-8
from django.db import models
from django.db.models import *
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.core.files.storage import FileSystemStorage
from django.db import IntegrityError, transaction

from .utils import *
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


class Qualification(Model):

    desc = TextField('描述')

    def __str__(self): return '%s' %  self.desc

    class Meta:
        ordering = ('pk',)
        verbose_name = verbose_name_plural = '认证条件'
    

class Institute(Model):

    name = CharField('机构名称', max_length=64, unique=True)
    province = CharField('省份', max_length=32)
    city = CharField('城市', max_length=32)
    logo = ImageField('公司图片', upload_to=UploadTo('institute/logo/%Y/%m'), blank=True)
    profile = TextField('机构介绍', blank=True)
    license = ImageField('营业执照', upload_to=UploadTo('institute/license/%Y/%m'), blank=True)
    orgcode = ImageField('组织机构代码证', upload_to=UploadTo('institute/orgcode/%Y/%m'), blank=True)
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
            osremove(item.license, self.license)
            osremove(item.orgcode,self.orgcode)


class User(Model):
   
    ''' 微信授权登录 '''
    openid = CharField('微信', max_length=64, unique=True, null=True, blank=True) # 微信授权登录的返回序列号
    photo = ImageField('图像', upload_to=UploadTo('user/photo/%Y/%m'), blank=True) # 微信的图像, 用户可以自己设置, 默认为微信没有的图像
    nickname = CharField('昵称', max_length=64, blank=True, default='匿名用户') # 微信的昵称, 用户可以自己设置, 默认为匿名用户 
    bg = ImageField('微信背景', upload_to=UploadTo('user/bg/%Y/%m/'), blank=True)

    ''' 手机登录 '''
    tel = CharField('手机', max_length=11, unique=True, validators=[validtel])
    passwd = CharField('密码', max_length=32)

    ''' 系统, 极光, 版本 '''
    os = ForeignKey('OS', verbose_name='系统', null=True, on_delete=PROTECT, blank=True) # 系统类别
    regid = CharField('唯一识别码', max_length=32, blank=True) # 极光推送
    version = CharField('版本', max_length=64, blank=True) # 版本号, 用户更新检测
    create_datetime = DateTimeField('注册时间', auto_now_add=True)

    ''' 必填信息 '''
    name = CharField('姓名', max_length=16, blank=True) # 真实姓名 cation
    idno = CharField('身份证号码', max_length=18, blank=True) # 身份证号码 cation 
    email = EmailField('邮件地址', max_length=64, blank=True) # 邮件地址
    
    ''' 可选信息 '''
    company = CharField('公司', max_length=64, blank=True) # cation
    position= CharField('职位', max_length=64, blank=True) # cation
    province = CharField('省份', max_length=16, blank=True) # 所在省份
    city = CharField('城市', max_length=32, blank=True) # 所在城市
    comment = TextField('备注信息', blank=True)

    ''' 自动维护 '''
    gender = NullBooleanField('性别("男")', default=None)
    birthplace = CharField('出生地', max_length=128, blank=True)
    birthday = DateField('生日', null=True, blank=True)

    ''' 认证信息 '''
    qualification = ManyToManyField('Qualification', verbose_name='认证条件', blank=True)
    Institute = ForeignKey('Institute', verbose_name='机构', null=True, blank=True)

    def save(self, *args, **kwargs): #密码的问题
        edit = self.pk
        if edit: user = User.objects.get(pk=self.pk)
        super(User, self).save(*args, **kwargs)
        if edit:
            osremove(user.photo, self.photo)
            osremove(user.bg, self.bg)
        else:
            SMS(self.tel, REGISTE).send()
            MAIL('用户注册', '%s 在 %s 注册' % (self.tel, timeformat(self.create_datetime)) ).send()

    def __str__(self):
        return '%s:%s' % (self.name, self.tel)

    class Meta:
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '注册用户'


class Company(Model):

    name = CharField('公司名称', max_length=64, unique=True)
    province = CharField('省份', max_length=32)
    city = CharField('城市', max_length=32)
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
    name = CharField('姓名', max_length=32)
    tel = CharField('手机', max_length=11, validators=[validtel])
    company = CharField('公司名称', max_length=64)
    vcr = CharField('vcr', max_length=64, blank=True)
    create_datetime = DateTimeField('添加时间', auto_now_add=True)
    valid = NullBooleanField('是否合法')

    def __str__(self): return '%s' % self.name

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '上传项目'


class Project(Model):

    upload = ForeignKey('Upload', verbose_name='上传项目', null=True, blank=True) # 关联项目

    ''' 项目所关联的公司 '''
    company = ForeignKey('Company', verbose_name='公司', on_delete=PROTECT, blank=True)
    video = URLField('视频地址', blank=True)
    tag = TextField('标签', blank=True)
   
    ''' 项目概况 '''
    img = ImageField('图片', upload_to=UploadTo('project/img/%Y/%m'), blank=True) 
    summary = CharField('项目概述', max_length=64, blank=True)
    detail = TextField('项目详情', blank=True)
    pattern = TextField('商业模式', blank=True)
    business = TextField('主营业务', blank=True)

    ''' 路演时的具体情况 '''
    planfinance = PositiveIntegerField('计划融资', blank=True)
    finance2get = PositiveIntegerField('已获得融资', blank=True)
    pattern = CharField('融资方式', max_length=32, blank=True)
    share2give = DecimalField('让出股份', max_digits=4, decimal_places=2, blank=True)
    quitway = CharField('退出方式', max_length=32, blank=True)
    usage = TextField('资金用途')
    investor2plan = PositiveIntegerField('股东人数', blank=True)
    leadfund = PositiveIntegerField('领投金额', blank=True)
    followfund = PositiveIntegerField('跟投金额', blank=True)
   
    ''' 时间 '''
    roadshow_start_datetime = DateTimeField('路演时间', blank=True)
    roadshow_stop_datetime = DateTimeField('路演结束', blank=True)
    finance_stop_datetime = DateTimeField('融资结束', blank=True)
    over = NullBooleanField('众筹完成')
    create_datetime = DateTimeField('创建时间', auto_now_add=True)

    ''' 人数情况 '''
    attend = ManyToManyField('User', related_name='attend', verbose_name='与会者', blank=True)
    like = ManyToManyField('User', related_name='like', verbose_name='点赞', blank=True)

    ''' 公司新闻 '''
    event = TextField('公司新闻')

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
    photo = ImageField('头像', upload_to=UploadTo('coremember/photo/%Y/%m'), blank=True)
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
    valid = NullBooleanField('是否合法', default=None)
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
            pj = self.project.summary
            am = self.amount
            text = INVEST_VALID_TRUE %(dt, pj, am)
            JG(text).single(ri); SMS().remind(tp, text)
            MAIL( '投资申请', '%s于%s投资"%s"%s万' %(tp, dt, pj, am) ).send()


class Collect(Model):

    project = ForeignKey(Project, verbose_name='项目')
    user = ForeignKey(User, verbose_name='收藏人')
    create_datetime = DateTimeField('收藏日期', auto_now_add=True)

    def __str__(self): return '%s/%s' % (self.user.name, self.project)

    class Meta:
        ordering = ('pk', )
        unique_together = (('project', 'user'),)
        verbose_name = verbose_name_plural = '项目收藏情况'


class Banner(Model):

    title = CharField('题目', max_length=16)
    project = OneToOneField('Project', verbose_name='项目', blank=True, null=True)
    img = ImageField('图片', upload_to=UploadTo('banner/img/%Y/%m'))
    url = URLField('链接地址', max_length=64, blank=True)
    create_datetime = DateTimeField('创建日期', auto_now=True)
    comment = TextField('备注信息', blank=True)

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
    company = CharField('公司', max_length=64)
    title = CharField('职位', max_length=64)
    photo = ImageField('图像', upload_to=UploadTo('thinktank/img/%Y/%m'))
    thumbnail = ImageField('小图', upload_to=UploadTo('thinktank/thumbnail/%Y/%m'))
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
            osremove(thinktank.img, self.img)
            osremove(thinktank.thumbnail, self.thumbnail)


class OS(Model): 
    name = CharField('系统名称', max_length=16, unique=True)
    
    def __str__(self): return '%s' % self.name

    class Meta: 
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '操作系统'


class Version(Model):
    edition = CharField('版本号', max_length=16)
    os = ForeignKey('OS', verbose_name='系统类型', on_delete=PROTECT)
    item = TextField('更新条目')
    url = URLField('地址')
    create_datetime = DateTimeField('创建日期', auto_now=True)

    def __str__(self): return '%s/%s' % (self.os, self.edition)

    class Meta:
        ordering = ('-pk',)
        unique_together = ('edition', 'os')
        verbose_name = verbose_name_plural = '版本'


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
    url = URLField('网页url', blank=True)
    name = CharField('网页名', max_length=128)
    source = CharField('来源', max_length=64, default='金指投')
    content = TextField('内容', max_length=256)
    sharecount = PositiveIntegerField('分享', default=0)
    readcount = PositiveIntegerField('阅读数', default=0)
    pub_date = DateField('发布时间', null=True, blank=True)
    create_datetime = DateTimeField('创建时间', auto_now_add=True)

    def __str__(self): return '%s' % self.title

    class Meta:
        ordering = ('-pk', )
        unique_together = ('title', 'pub_date')
        verbose_name = verbose_name_plural = '资讯'

class Topic(Model):
    project = ForeignKey('Project', verbose_name='项目', on_delete=PROTECT)
    user = ForeignKey('User', verbose_name='发表话题者', on_delete=PROTECT)
    content = CharField('内容', max_length=128)
    at = ForeignKey('self', verbose_name='@话题', null=True, blank=True, on_delete=PROTECT)
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
        if edit == False and self.at_topic:
            JG('%s 回复了你' % self.user.name, {'api': 'msg'}).single(self.at.user.regid)
            

class MsgType(Model):
    name = CharField('消息类型', max_length=32, unique=True)
    desc = CharField('描述', max_length=32, blank=True, null=True)

    def __str__(self):
        return '%s' % self.name

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '消息类型'

class Push(Model):
    msgtype = ForeignKey('MsgType', verbose_name='消息类型')
    user = ManyToManyField('User', verbose_name='推送给', blank=True)
    title = CharField('标题', max_length=32, default='金指投')
    content = CharField('内容', max_length=64)
    _id = PositiveIntegerField('对应的id', blank=True, null=True)
    url = URLField('地址', blank=True, default='www.jinzht.com')
    comment = CharField('备注', max_length=64, blank=True)
    valid = NullBooleanField('是否合法', default=None)
    create_datetime = DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return '%s,%s' % (self.id, self.msgtype.desc)

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '推送'

    def save(self, *args, **kwargs):
        edit = self.pk
        super(Push, self).save(*args, **kwargs)
        if self.valid == True:
            if self.msgtype.name == 'web':
                news = News.objects.filter(pk=self._id)
                if news: self.url = '%s/%s/%s' %(settings.RES_URL, settings.NEWS_URL_PATH, news[0].name)
            extras = {'api': self.msgtype.name,
                '_id': self._id,
                'url': self.url
            }
            if not self.user:
                JG(self.content, extras).all()
                queryset = User.objects.all()
            else:
                for user in self.user.all(): 
                    user.regid and JG(self.content, extras).single(user.regid)
                queryset = self.user.all() 
            try:
                for user in queryset:
                    with transaction.atomic(): Inform.objects.create(user=user, push=self)
            except IntegrityError as e: pass
                    
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
        if edit == False:
            if self.user == self.feeling.user: pass
            else:
                extras = {'api': 'feeling', 'id':self.feeling.id}
                JG('有人提及到您', extras).single(self.feeling.user.regid)
                self.at and self.at.user != self.feeling.user and  JG('有人回复了你', extras).single(self.at.user.regid)
