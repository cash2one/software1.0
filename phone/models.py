# coding: utf-8
from django.db import models
from django.db.models import *
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.core.files.storage import FileSystemStorage
from django.db import IntegrityError, transaction

from .utils import *

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

class Qualification(models.Model):
    desc = models.TextField('描述')

    def __str__(self):
        return '%s' %  self.desc

    class Meta:
        ordering = ('pk',)
        verbose_name = verbose_name_plural = '认证条件'
    

class FundSizeRange(models.Model):
    desc = models.CharField('描述', max_length=32)

    def __str__(self):
        return '%s' % self.desc

    class Meta:
        ordering = ('pk',)
        verbose_name = verbose_name_plural = '☏基金规模'

class User(models.Model):
    telephone = CharField('手机', max_length=11, unique=True, validators=[validate_telephone])
    password = CharField('密码', max_length=32)
    system = models.ForeignKey('System', verbose_name='系统', null=True, editable=False, on_delete=models.PROTECT)
    regid = models.CharField('唯一识别码', max_length=32, blank=True)
    company = models.ManyToManyField('Company', verbose_name='公司', blank=True)
    position= models.ManyToManyField('Position', verbose_name='职位', blank=True)
    img = models.ImageField('图像', upload_to=UploadTo('user/img/%Y/%m'),blank=True)
    idfore = models.ImageField('ID正', upload_to=UploadTo('user/idfore/%Y/%m'), blank=True)
    idback = models.ImageField('ID背', upload_to=UploadTo('user/idback/%Y/%m'), blank=True)
    gender = models.NullBooleanField('性别("男")', default=None)
    name = CharField('姓名', max_length=16, blank=True)
    weixin = CharField('微信', max_length=64, blank=True)
    province = models.CharField('省份', max_length=16, blank=True)
    city = models.CharField('城市', max_length=32, blank=True)
    comment = TextField('备注信息', blank=True)
    create_datetime = models.DateTimeField('注册时间', auto_now_add=True)

    def save(self, *args, **kwargs): #密码的问题
        edit = self.pk is not None
        if edit: user = User.objects.get(pk=self.pk)
        super(User, self).save(*args, **kwargs)
        if edit:
            osremove(user.img, self.img)
            osremove(user.idfore, self.idfore)
            osremove(user.idback, self.idback)
        else:
            MobSMS().remind(self.telephone, settings.REGISTER) 
            MAIL('用户注册', '%s 在 %s 注册' % (self.telephone, timeformat(self.create_datetime)) ).send()

    def __str__(self):
        return '%s:%s' % (self.name, self.telephone)

    class Meta:
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '注册用户'

class Position(models.Model):
    name = models.CharField('职位名称', max_length=16, unique=True)

    def __str__(self):
        return '%s' % self.name

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '职位选择'

class JoinShip(models.Model):
    user = models.ForeignKey('User', verbose_name='用户', on_delete=models.PROTECT)
    company = models.ForeignKey('Company', verbose_name='公司')
    join_date = models.DateField('加入公司的时间', blank=True, null=True)
    position = models.ManyToManyField('Position', verbose_name='职位', blank=True)
    valid = models.NullBooleanField('是否属实', default=None)
    comment = models.TextField('备注', blank=True)
    create_datetime = models.DateTimeField('添加时间', auto_now_add=True)

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        if edit: joinship = JoinShip.objects.get(pk=self.pk)
        super(JoinShip, self).save(*args, **kwargs)
        if edit:
            pass
        else:
            self.user.company.add(self.company)
            

    def delete(self):
        self.user.company.remove(self.company)
        return super(JoinShip, self).delete()

    def __str__(self):
        return '%s/%s' % (self.user, self.company) 

    class Meta:
        ordering = ('-pk',)
        unique_together = ('user', 'company')
        verbose_name = verbose_name_plural = '公司加入情况'


class Companystatus(models.Model):
    name = models.CharField('状态名称', max_length=64, unique=True)

    def __str__(self):
        return '%s' % self.name

    class Meta:
        ordering = ('pk',)
        verbose_name = verbose_name_plural = '公司状态'

class Industry(models.Model):
    name = models.CharField('行业类别', max_length=16, unique=True)
    valid = models.NullBooleanField('是否合法', default=None)

    def __str__(self):
        return '%s' % self.name

    class Meta:
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '行业一览表'

class Company(models.Model):
    name = models.CharField('公司名称', max_length=64, unique=True)
    province = models.CharField('省份', max_length=32)
    city = models.CharField('城市', max_length=32)
    logo = models.ImageField('公司图片', upload_to=UploadTo('company/logo/%Y/%m'), blank=True)
    profile = TextField('公司简介', blank=True)
    technology = CharField('核心产品及技术', max_length=64, blank=True)
    industry = models.ManyToManyField('Industry', verbose_name='所属行业')
    companystatus = models.ForeignKey('Companystatus', verbose_name='公司状态', on_delete=models.PROTECT)
    license = models.ImageField('营业执照', upload_to=UploadTo('company/license/%Y/%m'), blank=True)
    organizationcode = models.ImageField('组织机构代码证', upload_to=UploadTo('company/organizationcode/%Y/%m'), blank=True)
    homepage = models.URLField('网站主页', max_length=64, blank=True)
    contact_name = models.CharField('事务人', max_length=16, blank=True)
    contact_phone = CharField('联系手机', max_length=11, validators=[validate_telephone], blank=True)
    create_datetime = models.DateTimeField('添加时间', auto_now_add=True)

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        if edit: company = Company.objects.get(pk=self.pk)
        super(Company, self).save(*args, **kwargs)
        if edit:
            osremove(company.logo, self.logo)
            osremove(company.license, self.license)
            osremove(company.organizationcode,self.organizationcode)
        else:
            pass

    def __str__(self):
        return '%s' % self.name

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '公司'

class Roadshow(models.Model):
    company = models.ForeignKey('Company', verbose_name='公司', null=True, blank=True, on_delete=models.PROTECT)
    user = models.ForeignKey('User', verbose_name='申请人', on_delete=models.PROTECT)
    contact_name = models.CharField('联系人', max_length=16)
    contact_phone = CharField('联系电话', max_length=11, validators=[validate_telephone])
    vcr = models.URLField('vcr', blank=True)
    summary = models.TextField('项目概述', blank=True)
    valid = NullBooleanField('是否安排路演', default=None)
    reason = models.TextField('拒绝原因', blank=True)
    roadshow_datetime = models.DateTimeField('路演时间', blank=True, null=True)
    comment = models.TextField('备注信息', blank=True)
    create_datetime = models.DateTimeField('申请日期', auto_now_add=True)
    handle_datetime = models.DateTimeField('处理时间', auto_now=True)
    
    def __str__(self):
        return '%s/%s' % (self.user.telephone, self.user.name) 

    class Meta:
        unique_together = (('company', 'roadshow_datetime'))
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '路演申请情况Ⅰѫ'

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        if edit: roadshow = Roadshow.objects.get(pk=self.pk)
        super(Roadshow, self).save(*args, **kwargs)
        if edit:
            if roadshow.valid != self.valid:
                extras = {'api':'roadshow', 'url':'www.jinzht.com'}
                if self.valid == True:
                    text = '你的路演申请已安排'
                    JiGuang(text, extras).single(self.user.regid)
                    MobSMS().remind(self.user.telephone, text) 
                elif self.valid == False:
                    text = '您的路演申请提交失败'
                    JiGuang(text, extras).single(self.user.regid)
                    MobSMS().remind(self.user.telephone, text) 
        else:
            text = '%s于 %s 申请路演, 处理一下吧' % (self.user.telephone, timeformat())
            MAIL('路演申请', text).send()

class Investor(models.Model):
    user = models.ForeignKey('User', verbose_name='认证用户', on_delete=models.PROTECT)
    company = models.ForeignKey('Company', verbose_name='机构', blank=True, null=True, on_delete=models.PROTECT)
    position = models.CharField('职位', max_length=32, blank=True)
    card = models.ImageField('用户名片', upload_to=UploadTo('investor/card/%Y/%m'), blank=True)
    fundsizerange = models.ForeignKey('FundSizeRange', verbose_name="基金规模", null=True, blank=True, on_delete=models.PROTECT)
    industry = models.ManyToManyField('Industry', verbose_name='关注领域', blank=True)
    qualification = models.ManyToManyField('Qualification', verbose_name='认证条件')
    valid = models.NullBooleanField('是否合格', default=None)
    certificate_datetime = models.DateTimeField('认证日期', auto_now_add=True) # depracated
    reason = models.TextField('认证失败原因', blank=True)
    comment = models.TextField('备注', blank=True)
    create_datetime= models.DateTimeField('申请认证日期', auto_now_add=True) 
    handle_datetime = models.DateTimeField('处理时间', auto_now=True)

    def __str__(self):
        return '%s' % self.user 

    class Meta:
        unique_together = ('user', 'company')
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '投资人★★★'

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        if edit: investor = Investor.objects.get(pk=self.pk)
        super(Investor, self).save(*args, **kwargs)
        if edit:
            if investor.valid != self.valid:
                extras = {'api':'investor',
                    'url':'www.jinzht.com'
                }
                if self.valid == True:
                    text = '您的投资认证已经通过'
                    JiGuang(text, extras).single(self.user.regid) 
                    MobSMS().remind(self.user.telephone, text)
                elif self.valid == False:
                    text = '您的投资认证失败'
                    JiGuang(text, extras).single(self.user.regid) 
                    MobSMS().remind(self.user.telephone, text)
        else:
            text = '%s 于 %s 申请了认证, 是否给ta通过' %(self.user.telephone, timeformat())
            MAIL('认证申请', text).send()

class Project(models.Model):
    roadshow = models.OneToOneField('Roadshow', verbose_name='路演', null=True, blank=True)
    company = models.ForeignKey('Company', verbose_name='公司', on_delete=models.PROTECT)
    summary = models.CharField('项目概述', max_length=64)
    desc = TextField('项目描述')
    img = models.ImageField('图片', upload_to=UploadTo('project/img/%Y/%m'))
    thumbnail = models.ImageField('小图', upload_to=UploadTo('project/thumbnail/%Y/%m'))
    video = models.FileField('视频', upload_to=UploadTo('project/video/%Y/%m'), blank=True)
    url = models.URLField('视频地址', blank=True)
    model = models.TextField('商业模式')
    business = models.TextField('主营业务')
    service = models.TextField('产品服务', blank=True, null=True)
    planfinance = PositiveIntegerField('计划融资', default=0)
    finance2get = PositiveIntegerField('已获得融资', default=0)
    pattern = CharField('融资方式', max_length=32, default='股权融资')
    share2give = DecimalField('让出股份', max_digits=4, decimal_places=2, default=0)
    tmpshare = models.CharField('临时股份', max_length=16, default='3')
    quitway = CharField('退出方式', max_length=32)
    usage = TextField('资金用途')
    investor2plan = PositiveIntegerField('股东人数', default=0)
    participator2plan = models.PositiveIntegerField('报名人数', default=0)

    leadfund = models.PositiveIntegerField('领投金额', default=0)
    followfund = models.PositiveIntegerField('跟投金额', default=0)
    
    roadshow_start_datetime = models.DateTimeField('路演时间', blank=True, null=True)
    roadshow_stop_datetime = models.DateTimeField('路演结束', blank=True, null=True)
    finance_stop_datetime = models.DateTimeField('融资结束', blank=True, null=True)
    over = models.NullBooleanField('众筹完成', default=None)

    create_datetime = models.DateTimeField('创建时间', auto_now_add=True)
    tag = models.TextField('标签', blank=True)

    participators = ManyToManyField('User', related_name='project_participators', verbose_name='与会者', blank=True)
    investors = ManyToManyField('Investor', related_name='project_investors', verbose_name='投资人', blank=True)
    likers = ManyToManyField('User', related_name='project_likes', verbose_name='点赞', blank=True)
    voters  = models.ManyToManyField('User', related_name='project_voters', verbose_name='投票', blank=True)
    collectors = ManyToManyField('User', related_name='project_collects', verbose_name='收藏', blank=True)

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        if edit: project = Project.objects.get(pk=self.pk)
        super(Project, self).save(*args, **kwargs)
        if edit:
            osremove(project.img ,self.img)
            osremove(project.video ,self.video)

    def __str__(self):
        return '%s%s' % (self.pk, self.company)
    
    class Meta:
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '项目具体信息☏☏☏'

#class Reply(models.Model):
#    project = models.ForeignKey('Project', verbose_name='项目', on_delete=models.PROTECT)
#    user = models.ForeignKey('User', verbose_name='认证用户', on_delete=models.PROTECT)
#    msg = models.CharField('信息', max_length='128')
#    valid = models.NullBooleanField('是否合法', default=None)
#    create_datetime = models.DateTimeField('创建时间', auto_now_add=True)
#
#    def __str__(self):
#        return '%s/%s' % (self.user, self.project)
#
#    class Meta:
#        ordering = ('-pk',)
#        verbose_name = verbose_name_plural = '项目回复'

class ProjectEvent(models.Model):
    project = models.ForeignKey('Project', verbose_name='项目', on_delete=models.PROTECT)
    title = models.CharField('新闻标题', max_length=32)
    happen_datetime = models.DateTimeField('发生时间')
    detail = models.TextField('事件')
    create_datetime = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return '%s' % self.title

    class Meta:
        unique_together = (('title', 'happen_datetime'),)
        ordering = ('pk',)
        verbose_name = verbose_name_plural = '项目重大事件'

class CoreMember(models.Model):
    project = ForeignKey(Project, verbose_name='项目', on_delete=models.PROTECT)  
    name = CharField('姓名', max_length=32)
    img = ImageField('头像', upload_to=UploadTo('coremember/img/%Y/%m'), blank=True)
    title = CharField('职位', max_length=32)
    profile = TextField('简介')
    create_datetime = models.DateTimeField('创建时间', auto_now_add=True)

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        if edit:
            coremember = CoreMember.objects.get(pk=self.pk)
        super(CoreMember, self).save(*args, **kwargs)
        if edit:
            osremove(coremember.img, self.img)

    def __str__(self):
        return '%s' % self.project

    class Meta:
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '核心成员'

class ParticipateShip(models.Model):
    project = models.ForeignKey('Project', verbose_name='项目方', on_delete=models.PROTECT)
    user = models.ForeignKey('User', verbose_name='参加人', on_delete=models.PROTECT)
    valid = models.NullBooleanField('是否同意来现场', default=None) 
    reason = models.TextField('告知客户不能来现场原因', blank=True)
    comment = models.TextField('备注', blank=True)
    create_datetime = models.DateTimeField('申请参加日期', auto_now_add=True)
    handle_datetime = models.DateTimeField('处理时间', auto_now=True)

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        if edit: participateship = ParticipateShip.objects.get(pk=self.pk)
        super(ParticipateShip, self).save(*args, **kwargs)
        if edit:
            if participateship.valid != self.valid:
                extras = {'api':'participate', 'url':''}
                if self.valid == True:
                    text = '您的来现场申请通过审核' 
                    JiGuang(text, extras).single(self.user.regid) 
                    MobSMS().remind(self.user.telephone, text)
                elif self.valid == False:
                    text = '您的来现场申请未通过审核'
                    JiGuang(text, extras).single(self.user.regid) 
                    MobSMS().remind(self.user.telephone, text)
        else:
            text = '您的来现场申请已经提交, 请耐心等待审核'
            #MobSMS().remind(self.user.telephone, text)
            text = '%s 于 %s 申请来 %s' % (self.user.telephone, timeformat(), self.project.summary)
            MAIL(subject='来现场', text=text).send()
            MAIL(subject='来现场', text=text, to=settings.invest_manager).send()
            self.project.participators.add(self.user)

    def delete(self):
        self.project.participators.remove(self.user)
        super(ParticipateShip, self).delete()

    def __str__(self):
        return '%s' % self.project

    class Meta:
        ordering = ('-pk',)
        unique_together = (('project', 'user'), ('user', 'create_datetime'))
        verbose_name = verbose_name_plural = '来现场报名表'

class VoteShip(models.Model):
    project = models.ForeignKey('Project', verbose_name='项目方', on_delete=models.PROTECT)
    user = models.ForeignKey('User', verbose_name='认证用户', on_delete=models.PROTECT)
    comment = models.CharField('备注', max_length=64,  blank=True)
    create_datetime = models.DateTimeField('投票日期', auto_now_add=True)

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        if edit: voteship = VoteShip.objects.get(pk=self.pk)
        super(VoteShip, self).save(*args, **kwargs)
        if edit:
            pass
        else:
            self.project.voters.add(self.user)

    def delete(self):
        self.project.voters.remove(self.user)
        super(VoteShip, self).delete()

    def __str__(self):
        return '%s/%s' % (self.project, self,user)

    class Meta:
        ordering = ('-pk',)
        unique_together = ('project', 'user')
        verbose_name = verbose_name_plural = '投票'

class InvestShip(models.Model):
    project = ForeignKey('Project', verbose_name='项目方', on_delete=models.PROTECT)
    investor = ForeignKey('Investor', verbose_name='投资人', on_delete=models.PROTECT)
    invest_amount = PositiveIntegerField('投资金额')
    share2get = models.DecimalField('占用股份', max_digits=4, decimal_places=2, default=0)
    lead = models.NullBooleanField('是否领投', default=None)
    valid = models.NullBooleanField('是否合法', default=None)
    comment = TextField('备注', blank=True)
    create_datetime = models.DateTimeField('投资日期', auto_now_add=True)

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        super(InvestShip, self).save(*args, **kwargs)
        if edit:
            pass
        else:
            telephone = self.investor.user.telephone 
            name = self.project.summary
            regid = self.investor.user.regid
            text = '您投资%s项目%s万, 如有问题请联系 %s, 或致邮 %s' % (name, self.invest_amount, settings.Michael, settings.EMAIL) 
            MobSMS().remind(telephone, text)
            JiGuang(text).single(regid) 
            text = '%s 于 %s 投资 "%s", %s万' % (
                telephone, 
                timeformat(), 
                name, 
                self.invest_amount
            ) 
            MAIL('投资申请', text).send()
            self.project.investors.add(self.investor)
    
    def delete(self):
        self.project.investors.remove(self.investor)
        super(InvestShip, self).delete()

    def __str__(self):
        return '%s/%s/%s' % (self.project, self.investor, self.invest_amount)
    
    class Meta:
        unique_together = ('project', 'investor')
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '$$$投资关系$$$'
    
class LikeShip(models.Model):
    project = ForeignKey(Project, verbose_name='项目', on_delete=models.PROTECT)
    user = ForeignKey(User, verbose_name='点赞人', on_delete=models.PROTECT)
    comment = TextField('备注', blank=True)
    create_datetime = models.DateTimeField('点赞日期', auto_now_add=True)
    
    def save(self, *args, **kwargs):
        edit = self.pk is not None
        super(LikeShip, self).save(*args, **kwargs)
        if edit:
            pass
        else:
            self.project.likers.add(self.user)

    def delete(self):
        self.project.likes.remove(self.user)
        print('call delete', self.project.id)
        super(LikeShip, self).delete()

    def __str__(self):
        return '%s/%s' % (self.project, self.user)

    class Meta:
        ordering = ('-pk', )
        unique_together = (('project', 'user'),)
        verbose_name = verbose_name_plural = '项目点赞情况'

class CollectShip(models.Model):
    project = ForeignKey(Project, verbose_name='项目', on_delete=models.PROTECT)
    user = ForeignKey(User, verbose_name='收藏人', on_delete=models.PROTECT)
    comment = TextField('备注', blank=True)
    create_datetime = models.DateTimeField('收藏日期', auto_now_add=True)

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        super(CollectShip, self).save(*args, **kwargs)
        if edit:
            pass
        else:
            self.project.collectors.add(self.user)

    def delete(self):
        self.project.collectors.remove(self.user)
        super(CollectShip, self).delete()

    def __str__(self):
        return '%s/%s' % (self.user.name, self.project)

    class Meta:
        ordering = ('pk', )
        unique_together = (('project', 'user'),)
        verbose_name = verbose_name_plural = '项目收藏情况'

class RecommendProject(models.Model):
    project = models.OneToOneField('Project', verbose_name='项目')
    reason = models.TextField('推荐理由')
    star = models.PositiveSmallIntegerField('推荐指数')
    start_datetime = models.DateTimeField('开始日期')
    end_datetime   = models.DateTimeField('截至日期')
    create_datetime = models.DateTimeField('创建日期', auto_now_add=True)

    def __str__(self):
        return '%s/%s' % (self.project, self.star)

    class Meta:
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '推荐项目'

class BannerType(models.Model):
    name = models.CharField('旗标类型', max_length=16, unique=True)

    def __str__(self):
        return '%s' % self.name

    class Meta:
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '旗标类型'

class Banner(models.Model):
    title = models.CharField('题目', max_length=16)
    img = models.ImageField('图片', upload_to=UploadTo('banner/img/%Y/%m'))
    project = models.OneToOneField('Project', verbose_name='项目', blank=True, null=True)
    url = models.URLField('链接地址', max_length=64, blank=True)
    desc = models.TextField('介绍', blank=True)
    create_datetime = models.DateTimeField('创建日期', auto_now_add=True)

    def __str__(self):
        return '%s' % self.title

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '旗标栏'

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        if edit: banner = Banner.objects.get(pk=self.pk)
        super(Banner, self).save(*args, **kwargs)
        if edit:
            osremove(banner.img, self.img) 


class Thinktank(models.Model):
    name = models.CharField('姓名', max_length=16)
    company = models.CharField('公司', max_length=64)
    title = models.CharField('职位', max_length=64)
    thumbnail = models.ImageField('图像', upload_to=UploadTo('thinktank/thumbnail/%Y/%m'))
    img = models.ImageField('图像', upload_to=UploadTo('thinktank/img/%Y/%m'))
    video = models.URLField('链接地址', max_length=64, blank=True)
    experience = models.TextField('经历')
    success_cases = models.TextField('成功案例')
    good_at_field = models.TextField('擅长领域')
    create_datetime = models.DateTimeField('创建日期', auto_now_add=True)

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        if edit: thinktank = Thinktank.objects.get(pk=self.pk)
        super(Thinktank, self).save(*args, **kwargs)
        if edit:
            osremove(thinktank.img, self.img)
            osremove(thinktank.thumbnail, self.thumbnail)

    def __str__(self):
        return '%s' % self.name

    class Meta:
        ordering = ('pk',)
        verbose_name = verbose_name_plural = '智囊团'

class ThinktankCollect(models.Model):
    thinktank = models.ForeignKey('Thinktank', verbose_name='智囊', on_delete=models.PROTECT)
    user = models.ForeignKey('User', verbose_name='用户', on_delete=models.PROTECT)
    create_datetime = models.DateTimeField('收藏日期', auto_now_add=True)

    def __str__(self):
        return '%s' % (self.thinktank)
    class Meta:
        ordering = ('-pk', )
        unique_together = ('user', 'thinktank')
        verbose_name = verbose_name_plural = '智囊团收藏'

class System(models.Model):
    name = models.CharField('系统名称', max_length=16, unique=True)
    
    def __str__(self):
        return '%s' % self.name

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '操作系统'

class Version(models.Model):
    edition = models.CharField('版本号', max_length=16)
    system = models.ForeignKey('System', verbose_name='系统类型', on_delete=models.PROTECT)
    item = models.TextField('更新条目')
    href = models.URLField('地址')
    create_datetime = models.DateTimeField('创建日期', auto_now=True)

    def __str__(self):
        return '%s/%s' % (self.system, self.edition)

    class Meta:
        ordering = ('-pk',)
        unique_together = ('edition', 'system')
        verbose_name = verbose_name_plural = '版本'

class Informlist(models.Model):
    project = models.ForeignKey('Project', verbose_name='项目', on_delete=models.PROTECT)
    user = models.ForeignKey('User', verbose_name='举报人', on_delete=models.PROTECT)
    reason = models.TextField('举报原因')
    valid = models.NullBooleanField('是否真实')
    msg = models.TextField('回显信息')
    comment = models.TextField('备注', blank=True)
    create_datetime = models.DateTimeField('举报时间', auto_now_add=True)

    def __str__(self):
        return '%s' % self.project 

    class Meta:
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '举报'


class Blacklist(models.Model):
    user = models.ForeignKey('User', verbose_name='黑名人', on_delete=models.PROTECT)
    reason = models.TextField('黑名原因')
    comment = models.CharField('备注', max_length=32, blank=True)
    create_datetime = models.DateTimeField('黑名时间', auto_now_add=True)

    def __str__(self):
        return '%s' % self.user

    class Meta:
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '黑名单'

class Activity(models.Model):
    summary = models.CharField('活动概述', max_length=32)
    start_datetime = models.DateTimeField('开始时间')
    stop_datetime = models.DateTimeField('结束时间')
    desc = models.TextField('活动描述', blank=True)
    coordinate = models.CharField('地点', max_length=128)
    latitude = models.DecimalField('纬度', max_digits=8, decimal_places=6)
    longitude = models.DecimalField('经度', max_digits=9, decimal_places=6)
    comment = models.CharField('备注', max_length=32, blank=True)
    create_datetime = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return '%s' % self.summary

    class  Meta:
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '活动'

class Signin(models.Model):
    user = models.ForeignKey('User', verbose_name='签到人', on_delete=models.PROTECT)
    activity = models.ForeignKey('Activity', verbose_name='活动', on_delete=models.PROTECT)
    signin_datetime = models.DateTimeField('签到日期', auto_now_add=True)
    signout_datetime = models.DateTimeField('签出日期', null=True, blank=True)
    comment = models.TextField('备注', blank=True)

    def __str__(self):
        return '%s' % self.user

    class Meta:
        unique_together = (('user', 'activity'),)
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '签到'

class NewsType(models.Model):
    name = models.CharField('资讯类型名', max_length=16, unique=True)
    valid = models.NullBooleanField('是否真实', default=None)
    eng = models.CharField('对应英文', max_length=64)

    
    def __str__(self):
        return '%s' % self.name

    class Meta:
        ordering = ('-pk', )
        verbose_name = verbose_name_plural = '资讯类型'
    
class News(models.Model):
    newstype = models.ForeignKey('NewsType', verbose_name='资讯类型', blank=True, null=True, default=1)
    title = models.CharField('标题', max_length=64)
    src = models.URLField('图片url', blank=True)
    href = models.URLField('网页url', blank=True)
    name = models.CharField('网页名', max_length=128)
    source = models.CharField('来源', max_length=64, default='金指投')
    content = models.TextField('内容', max_length=256)
    keyword = models.CharField('关键词', max_length=64)
    sharecount = models.PositiveIntegerField('分享', default=0)
    readcount = models.PositiveIntegerField('阅读数', default=0)
    pub_date = models.DateField('发布时间', null=True, blank=True)
    create_datetime = models.DateTimeField('创建时间', auto_now_add=True)
    valid = models.NullBooleanField('合法', default=None)

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        if edit: news = News.objects.get(pk=self.pk)
        super(News, self).save(*args, **kwargs)

    def __str__(self):
        return '%s' % self.title

    class Meta:
        ordering = ('-pk', )
        unique_together = ('title', 'pub_date')
        verbose_name = verbose_name_plural = '资讯'

class KnowledgeType(models.Model):
    pass

class Knowledge(models.Model):
    pass

class Keyword(models.Model):
    word = models.CharField('热词', max_length=16, unique=True)
    hotgrade= models.PositiveIntegerField('热度', default=0)
    comment = models.CharField('备注', max_length=64, blank=True)
    create_datetime = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return '%s' % self.word

    class Meta:
        ordering = ('pk', )
        verbose_name = verbose_name_plural = '热词'
    

class Topic(models.Model):
    project = models.ForeignKey('Project', verbose_name='项目', on_delete=models.PROTECT)
    user = models.ForeignKey('User', verbose_name='发表话题者', on_delete=models.PROTECT)
    content = models.CharField('内容', max_length=128)
    at_topic = models.ForeignKey('self', verbose_name='@话题', null=True, blank=True, on_delete=models.PROTECT)
    valid = models.NullBooleanField('是否真实', default=None)
    read = models.NullBooleanField('是否阅读', default=False)
    create_datetime = models.DateTimeField('创建时间', auto_now_add=True)
   
    def __str__(self):
        return '%s' % self.content

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '话题'

class Feedback(models.Model):
    user = models.ForeignKey('User', verbose_name='用户')
    advice = models.TextField('用户吐槽')
    valid = models.NullBooleanField('是否合法', default=None)
    comment = models.CharField('备注', max_length=64, blank=True)
    create_datetime = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return '%s/%s' % (self.user, self.advice)

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '用户反馈'

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        if not edit:
            MobSMS().remind(self.user.telephone, '感谢你对金指投的支持, 我们会第一时间处理你的建议')
        super(Feedback, self).save(*args, **kwargs)

class Aboutus(models.Model):
    title = models.CharField('标题', max_length=32)
    img = models.ImageField('图片', upload_to=UploadTo('aboutus/img/%Y/%m'))
    content = models.TextField('内容')
    create_datetime = models.DateTimeField('创建时间', auto_now_add=True)

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        if edit: aboutus = Aboutus.objects.get(pk=self.pk)
        super(Aboutus, self).save(*args, **kwargs)
        if edit: osremove(aboutus.img, self.img)

    def __str__(self):
        return '%s' % self.title

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '关于我们的分享'

class MsgType(models.Model):
    name = models.CharField('消息类型', max_length=32, unique=True)

    def __str__(self):
        return '%s' % self.name

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '消息类型'

class Push(models.Model):
    msgtype = models.ForeignKey('MsgType', verbose_name='消息类型')
    user = models.ManyToManyField('User', verbose_name='推送给', blank=True)
    title = models.CharField('标题', max_length=32, default='金指投')
    content = models.CharField('内容', max_length=64)
    _id = models.PositiveIntegerField('对应的id', blank=True, null=True)
    url = models.URLField('地址', blank=True, default='www.jinzht.com')
    comment = models.CharField('备注', max_length=64, blank=True)
    valid = models.NullBooleanField('是否合法', default=None)
    create_datetime = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return '%s' % self.title

    class Meta:
        ordering = ('-pk',)
        verbose_name = verbose_name_plural = '推送'

    def save(self, *args, **kwargs):
        edit = self.pk is not None
        if self.valid == True:
            if self.msgtype.name == 'web':
                news = News.objects.filter(pk=self._id)
                if news: self.url = '%s/%s/%s' %(settings.RES_URL, settings.NEWS_URL_PATH, news[0].name)
            extras = {'api': self.msgtype.name,
                '_id': self._id,
                'url': self.url
            }
            if not self.user:
                JiGuang(self.content, extras).all()
                queryset = User.objects.all()
            else:
                for user in self.user.all(): 
                    user.regid and JiGuang(self.content, extras).single(user.regid)
                queryset = self.user.all() 
            try:
                for user in queryset:
                    with transaction.atomic(): Msgread.objects.create(user=user, push=self)
            except IntegrityError as e: pass
        super(Push, self).save(*args, **kwargs)
                    
class Msgread(models.Model):
    user = models.ForeignKey('User', verbose_name='用户')
    push = models.ForeignKey('Push', verbose_name='push')
    read = models.NullBooleanField('是否阅读', default=False)
    create_datetime = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return '%s' % self.user

    class Meta:
        ordering = ('-pk',)
        unique_together = ('user', 'push')
        verbose_name = verbose_name_plural = '消息阅读'
