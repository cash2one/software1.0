# coding: utf-8
from django.contrib import admin
from django.contrib import messages

from .modelform import *

class QualificationAdmin(admin.ModelAdmin):
    form = QualificationForm
    list_display = ('id', 'desc')

class FundSizeRangeAdmin(admin.ModelAdmin):
    form = FundSizeRangeForm
    list_display = ('id', 'desc')
    fields = ('desc',)

class UserAdmin(admin.ModelAdmin):

    form = UserForm
    list_display = ('id', 'name', 'telephone', 'gender', 'province_city', '_company', '_create_datetime')
    raw_id_fields = ('company', 'position')
    search_fields = ('telephone',)

    def province_city(self, obj):
        return '%s %s' % (obj.province, obj.city)

    def _company(self, obj):
        return ','.join([company.name for company in obj.company.all()])

    def _create_datetime(self, obj):
        return timeformat(obj.create_datetime)

    def has_delete_permission(self, request, obj=None):
        return True
        return False

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return super(UserAdmin, self).change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        return super(UserAdmin, self).add_view(request, form_url, extra_context)

    def get_actions(self, request):
        actions = super(UserAdmin, self).get_actions(request)
        return actions

class PositionAdmin(admin.ModelAdmin):
    form = PositionForm

class JoinShipAdmin(admin.ModelAdmin):
    form = JoinShipForm
    list_display = ('user', 'company', 'join_date', '_position', 'valid')
    list_editable = ('valid', )
    raw_id_fields = ('user', 'company')
    actions = ['delete_and_update']

    def save_model(self, request, obj, form, change):
        if change:
            if 'company' in form.changed_data or 'user' in form.changed_data:
                return messages.error(request, '✖ %s' %(JoinShip._meta.verbose_name.title()))
        obj.save()
                
    def _position(self, obj):
        return ','.join( [o.name for o in obj.position.all()])

    def get_actions(self, request):
        actions = super(JoinShipAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def delete_and_update(self, request, queryset):
        for item in queryset:
            item.delete()
            print('after delete')

class CompanystatusAdmin(admin.ModelAdmin):
    form = CompanystatusForm
    list_display = ('id', 'name')

class IndustryAdmin(admin.ModelAdmin):
    form = IndustryForm
    list_display = ('id', 'name', 'valid')
    list_editable = ('valid',)

class CompanyAdmin(admin.ModelAdmin):
    form = CompanyForm
    list_display = ('id', 'name', 'logo', '_license', 'organizationcode','industry_name', 'companystatus', 'contact_name', 'contact_phone')
    raw_id_fields = ('industry',) 
    def _license(self, obj):
        if not obj.license: return None
        return '<img width="150px" src="%s"/>' % obj.license.url 
    _license.allow_tags = True
    _license.short_description = '营业执照'

    def industry_name(self, obj):
        return ','.join([o.name for o in obj.industry.all()])
    industry_name.short_description = '行业'

    def add_view(self, request, form_url='', extra_context=None):
        return super(CompanyAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return super(CompanyAdmin, self).change_view(request, object_id, form_url, extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            if hasattr(self, 'queryset'):
                kwargs['queryset'] = self.queryset
        return super(CompanyAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

   
class RoadshowAdmin(admin.ModelAdmin):
    form = RoadshowForm
    list_display = ('id', 'user', 'company', 'contact_name', 'contact_phone', 'vcr', 'create_datetime', 'summary', 'valid', 'roadshow_datetime')
    list_editable = ('valid',)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.queryset = Company.objects.filter(roadshow__pk=object_id)
        return super(RoadshowAdmin, self).change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        self.queryset = Company.objects.filter(Q(roadshow__isnull=True) | ~Q(roadshow__valid=False) & ~Q(roadshow__valid=None)).distinct()
        return super(RoadshowAdmin, self).add_view(request, form_url, extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'company':
            if hasattr(self, 'queryset'):
                kwargs['queryset'] = self.queryset
        return super(RoadshowAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


    def get_actions(self, request):
        actions = super(RoadshowAdmin, self).get_actions(request)
        return actions

class InvestorAdmin(admin.ModelAdmin):
    form = InvestorForm
    list_display = ('id', 'user', 'investor_type', 'company', 'fundsizerange', 'valid', 'create_datetime', 'certificate_datetime')
    raw_id_fields = ('industry',)
    list_editable = ('valid',)
    def investor_type(self, obj):
        if obj.company:
            return '机构投资人'
        else:
            return '自然投资人'

    def save_model(self, request, obj, form, change):
        user = request.user.username
        print('user', user)
        if user == 'view':
            messages.error(request, '您没有修改权限')
            return
        obj.save()

    def add_view(self, request, form_url='', extra_context=None):
        return super(InvestorAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.queryset = User.objects.filter( investor__pk=object_id )
        return super(InvestorAdmin, self).change_view(request, object_id, form_url, extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            if hasattr(self, 'queryset'):
                kwargs['queryset'] = self.queryset
        return super(InvestorAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


class ProjectAdmin(admin.ModelAdmin):
    form = ProjectForm
    list_display = ('id', '_stage', 'summary', 'company', 'planfinance', 'finance2get', '_leadfollow', 'tmpshare', 'share2give', 'investor2plan', '_roadshow_start_datetime', '_finance_stop_datetime', 'thumbnail')
    raw_id_fields = ('roadshow', 'company', 'participators', 'investors', 'likers', 'voters', 'collectors')
    list_editable = ('thumbnail', 'finance2get',)
    def _leadfollow(self, obj):
        return '%s/%s' % (obj.leadfund, obj.followfund)
    _leadfollow.short_description = '领/跟投'

    def _stage(self, obj):
        now = timezone.now()
        if not obj.roadshow_start_datetime or now < obj.roadshow_start_datetime:
            stage = '路演预告'
            return None
        elif now > obj.roadshow_stop_datetime:
            if now > obj.finance_stop_datetime:
                stage = '融资完毕'
                return True
            else:
                stage = '融资进行'
                return False
        else:
            stage = '融资进行'
            return False

        return stage
    _stage.short_description = '状态'
    _stage.boolean = True

    def _roadshow_start_datetime(self, obj):
        return timeformat(obj.roadshow_start_datetime)
    _roadshow_start_datetime.short_description='路演时间'

    def _finance_stop_datetime(self, obj):
        return timeformat(obj.finance_stop_datetime)
    _finance_stop_datetime.short_description='融资截至'
    fieldsets = (
        (None, {
            'fields':(('roadshow', 'company'), 'summary', 'img', 'thumbnail', 'video', 'url') 
        }),

        ('内容', {
            'fields':('desc', 'model', 'business', 'service')
        }),
        ('融资', {
            'fields':(('planfinance', 'finance2get', 'pattern', 'tmpshare', 'share2give', 'quitway'), 'usage')
        }),
        ('数字', {
            'fields':(('investor2plan', 'participator2plan', 'leadfund', 'followfund'),)
        }),
        ('时间', {
            'fields':(('roadshow_start_datetime', 'roadshow_stop_datetime', 'finance_stop_datetime'), 'over')
        }),
        ('人', {
            'fields':('participators', 'investors', 'likers', 'voters', 'collectors'),
            'classes':('collapse',)
        })
    )

class ProjectEventAdmin(admin.ModelAdmin):
    change_form_template = 'phone/admin/change_form.html'
    form = ProjectEventForm
    list_display = ('id',
                    'project',
                    'title',
                    'happen_datetime',
                    'detail',
            )

class CoreMemberAdmin(admin.ModelAdmin):
    form = CoreMemberForm
    list_display = ('id', 'project', 'name', '_img', 'title')
    #list_editable = ('img',)
    def _img(self, obj):
        if obj.img:
            return '<img width="50px" src="%s"/>' % obj.img.url
        return '<img width="50px" src="%s"/>' % 'http://www.jinzht.com/media/default/coremember.png'
    _img.allow_tags = True
    _img.short_description = '图像'

class ParticipateShipAdmin(admin.ModelAdmin):
    form = ParticipateShipForm
    list_display = ('id', 'project', 'user', 'create_datetime', 'valid')
    list_editable = ('valid',)
    
    def save_model(self, request, obj, form, change):
        if change:
            if 'project' in form.changed_data or 'user' in form.changed_data:
                return messages.error(request, '✖ %s' %(ParticipateShip._meta.verbose_name.title()))
        obj.save()

    def add_view(self, request, form_url='', extra_context=None):
        self.project = Project.objects.filter(roadshow_datetime__gte=timezone.now()-timedelta(days=3))
        return super(ParticipateShipAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.project = Project.objects.filter(participateship__pk=object_id)
        return super(ParticipateShipAdmin, self).change_view(request, object_id, form_url, extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'project':
            if hasattr(self, 'project'):
                kwargs['queryset'] = self.project
        return super(ParticipateShipAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
            

class InvestShipAdmin(admin.ModelAdmin):
    form = InvestShipForm
    list_display = ('id', 'project', 'investor', 'invest_amount', 'share2get', 'valid')
    list_editable = ('valid',)
    raw_id_fields = ('project', 'investor')

    def save_model(self, request, obj, form, change):
        if change:
            if 'project' in form.changed_data or 'investor' in form.changed_data:
                return messages.error(request, '✖ %s' %(InvestShip._meta.verbose_name.title()))
        obj.save()

    def add_view(self, request, form_url='', extra_context=None):
        #self.investor = User.objects.filter( Q(investor__isnull=False) | Q(investor__isnull=False) ) 
        return super(InvestShipAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.project = Project.objects.filter(investship__pk=object_id)
        self.investor = Investor.objects.filter(investship__pk=object_id)
        return super(InvestShipAdmin, self).change_view(request, object_id, form_url, extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'investor':
            if hasattr(self, 'investor'):
                kwargs['queryset'] = self.investor
        return super(InvestShipAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

class VoteShipAdmin(admin.ModelAdmin):
    form = VoteShipForm
    list_display = ('id', 'project', 'user')

    def save_model(self, request, obj, form, change):
        if change:
            if 'project' in form.changed_data or 'user' in form.changed_data:
                return messages.error(request, '✖ %s' %(VoteShip._meta.verbose_name.title()))
        obj.save()

class LikeShipAdmin(admin.ModelAdmin):
    form = LikeShipForm
    list_display = ('id', 'project', 'user',)
    fields = ('project', 'user')

    def save_model(self, request, obj, form, change):
        if change:
            if 'project' in form.changed_data or 'user' in form.changed_data:
                return messages.error(request, '✖ %s' %(LikeShip._meta.verbose_name.title()))
        obj.save()

class CollectShipAdmin(admin.ModelAdmin):
    form = CollectShipForm
    list_display = ('id', 'project', 'user')
    fields = ('project', 'user')

    def save_model(self, request, obj, form, change):
        if change:
            if 'project' in form.changed_data or 'user' in form.changed_data:
                return messages.error(request, '✖ %s' %(CollectShip._meta.verbose_name.title()))
        obj.save()

class RecommendProjectAdmin(admin.ModelAdmin):
    form = RecommendProjectForm
    list_display = ('id', 'project', 'reason', 'star', 'start_datetime', 'end_datetime')
   
    def add_view(self, request, form_url='', extra_context=None):
        self.project = Project.objects.filter(recommendproject__isnull=True)
        return super(RecommendProjectAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, object_id, request, form_url='', extra_context=None):

        return super(RecommendProjectAdmin, self).change_view(object_id, request, form_url, extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'project':
            if hasattr(self, 'project'):
                kwargs['queryset'] = self.project

        return super(RecommendProjectAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


class BannerTypeAdmin(admin.ModelAdmin):
    form = BannerTypeForm
    list_display = ('id', 'name')

class BannerAdmin(admin.ModelAdmin):
    form = BannerForm
    list_display = ('id', 'title', 'img', 'desc', 'url')

class ThinktankAdmin(admin.ModelAdmin):
    form = ThinktankForm
    list_display = ('id', 'name', 'title', '_img')
    def _img(self, obj):
        return '<a target="_blank" href="%s">img</a>' % (obj.img.url)
    _img.allow_tags = True
    _img.short_description = '图像'

class ThinktankCollectAdmin(admin.ModelAdmin):
    form = ThinktankCollectForm
    list_display = ('id', 'user', 'thinktank')


class SystemAdmin(admin.ModelAdmin):
    form = SystemForm
    list_display = ('id', 'name')

class VersionAdmin(admin.ModelAdmin):
    form = VersionForm
    list_display = ('id', 'edition', 'system', 'create_datetime')

class InformlistAdmin(admin.ModelAdmin):
    form = InformlistForm
    list_display = ('id', 'project', 'user', 'reason', 'create_datetime', 'valid', 'msg')

class BlacklistAdmin(admin.ModelAdmin):
    form = BlacklistForm
    list_display = ('id', 'user', 'create_datetime', 'reason')

class SigninAdmin(admin.ModelAdmin):
    form = SigninForm
    list_display = ('id', 'user', 'signin_datetime', 'signout_datetime')

class ActivityAdmin(admin.ModelAdmin):
    form = ActivityForm
    list_display = ('id', 'summary', 'start_datetime', 'stop_datetime', 'coordinate', 'longitude', 'latitude')
    exclude = ('create_datetime',)

class NewsTypeAdmin(admin.ModelAdmin):
    form = NewsTypeForm
    list_display = ('id', 'name', 'eng', 'valid')
    list_editable = ('eng', 'valid')

class NewsAdmin(admin.ModelAdmin):
    form = NewsForm 
    list_display = ('id', 'title',)

class KnowledgeTypeAdmin(admin.ModelAdmin):
    form = KnowledgeTypeForm
    
class KnowledgeAdmin(admin.ModelAdmin):
    form = KnowledgeForm

class KeywordAdmin(admin.ModelAdmin):
    form = KeywordForm
    list_display = ('id', 'word', 'hotgrade')

class TopicAdmin(admin.ModelAdmin):
    form = TopicForm
    list_display = ('id', 'project', 'user', 'at_user', 'content', 'read')
    raw_id_fields = ('project', 'user', 'at_topic')
    list_editable = ('read',)
    def at_user(self, obj):
        if obj.at_topic:
            return obj.at_topic.user.name
        return ''

class FeedbackAdmin(admin.ModelAdmin):
    form = FeedbackForm
    list_display = ('id', 'user', 'advice')

class AboutusAdmin(admin.ModelAdmin):
    form = AboutusForm
    list_display = ('id', 'title', 'img')

class MsgTypeAdmin(admin.ModelAdmin):
    form = MsgTypeForm
    list_display = ('id', 'name')

class PushAdmin(admin.ModelAdmin):
    form = PushForm
    list_display = ('id', 'msgtype', '_id', '_user', 'valid')
    raw_id_fields = ('user',)
    def _user(self, obj):
       return ','.join([user.telephone for user in obj.user.all()]) 
    list_editable = ('valid',)

class MsgreadAdmin(admin.ModelAdmin):
    form = MsgreadForm
    list_display = ('id', 'user', 'push', 'read')
    
