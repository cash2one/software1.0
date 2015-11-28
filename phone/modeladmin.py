# coding: utf-8
from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html

from .modelform import *

class InstituteAdmin(admin.ModelAdmin):
    form = InstituteForm

class UserAdmin(admin.ModelAdmin):
    form = UserForm
    list_display = ('id', 'name', 'tel', 'gender', 'addr', 'company', '_create_datetime', 'qualification', 'valid')
    search_fields = ('tel',)
    list_editable = ('valid',)
    
    #readonly_fields = ('idpic', '_idpic', 'photo', '_photo', 'nickname', 'name', 'tel', 'passwd', 
    #    'gender', 'idno',  'email', 'company', 'position', 
    #    'addr', 'birthday', 'birthplace', 
    #    #'bg', 'openid', 'os', 'regid', 'version', 
    #    'bg', 'os', 'regid', 'version', 
    #    'lastlogin', 'qualification')
    
    def _photo(self, obj):
        if  obj.photo:
            url = obj.photo.url
        else:
            url = ''
        return  format_html('<img width="200px" src="%s"/>' % url)
    _photo.allow_tags = True
    _photo.short_description = 'photo'

    def _idpic(self, obj):
        if  obj.idpic:
            url = obj.idpic.url
        else:
            url = ''
        return  format_html('<img width="200px" src="%s"/>' % url)
    _idpic.allow_tags = True
    _idpic.short_description = '身份证'

    def _create_datetime(self, obj):
        return timeformat(obj.create_datetime)

   # def has_delete_permission(self, request, obj=None):
   #     return True

   # def change_view(self, request, object_id, form_url='', extra_context=None):
   #     return super(UserAdmin, self).change_view(request, object_id, form_url, extra_context)

   # def add_view(self, request, form_url='', extra_context=None):
   #     return super(UserAdmin, self).add_view(request, form_url, extra_context)

   # def get_actions(self, request):
   #     actions = super(UserAdmin, self).get_actions(request)
   #     return actions


class CompanyAdmin(admin.ModelAdmin):
    form = CompanyForm
    list_display = ('id', 'name', 'logo', '_license', 'orgcode')
    def _license(self, obj):
        if not obj.license: return None
        return '<img width="150px" src="%s"/>' % obj.license.url 
    _license.allow_tags = True
    _license.short_description = '营业执照'

    def add_view(self, request, form_url='', extra_context=None):
        return super(CompanyAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return super(CompanyAdmin, self).change_view(request, object_id, form_url, extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            if hasattr(self, 'queryset'):
                kwargs['queryset'] = self.queryset
        return super(CompanyAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

class UploadAdmin(admin.ModelAdmin):
    form = UploadForm
    list_display = ('id', 'user', 'vcr', 'valid')
    list_editable = ('valid', )

class ProjectAdmin(admin.ModelAdmin):
    form = ProjectForm
    list_display = ('id', 'stage', 'company', 'planfinance', 'finance2get', 'share2give', 'invest2plan', 'start', 'stop', 'img')
    raw_id_fields = ('company', 'attend', 'like')
    list_editable = ('img', 'finance2get',)


    def stage(self, obj):
        now = timezone.now()
        if not obj.start or now < obj.start: 
            return None # 路演预告
        elif now > obj.stop:
            return True
        else: 
            return False # 融资进行

        return stage
    stage.short_description = '状态'
    stage.boolean = True

    def start(self, obj):
        return timeformat(obj.start)
    start.short_description='开始时间'

    def stop(self, obj):
        return timeformat(obj.stop)
    stop.short_description='融资截至'

    fieldsets = (
        (None, {
            'fields':('company', 'upload', 'img', 'video') 
        }),

        ('内容', {
            'fields':('model', 'business', 'tag')
        }),
        ('融资', {
            'fields':(('planfinance', 'finance2get', 'share2give', 'quitway'), 'usage')
        }),
        ('新闻', {
            'fields': ('event',)
        }),
        ('数字', {
            'fields':(('invest2plan', 'minfund'),)
        }),
        ('时间', {
            'fields':(('start', 'stop'), 'over')
        }),
        ('人', {
            'fields':('attend', 'like'),
            'classes':('collapse',)
        })
    )


class MemberAdmin(admin.ModelAdmin):
    form = MemberForm
    list_display = ('id', 'project', 'name', '_img', 'position')
    def _img(self, obj):
        if obj.photo:
            return '<img width="50px" src="%s"/>' % obj.photo.url
        return '<img width="50px" src="%s"/>' % 'http://www.jinzht.com/media/default/coremember.png'
    _img.allow_tags = True
    _img.short_description = '图像'

class InvestAdmin(admin.ModelAdmin):
    form = InvestForm
    list_display = ('id', 'project', 'user', 'amount', 'valid')
    list_editable = ('valid',)
    #raw_id_fields = ('project', 'user')

    def save_model(self, request, obj, form, change):
        if change:
            if 'project' in form.changed_data or 'investor' in form.changed_data:
                return messages.error(request, '✖ %s' %(Invest._meta.verbose_name.title()))
        obj.save()

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.project = Project.objects.filter(invest__pk=object_id)
        return super(InvestAdmin, self).change_view(request, object_id, form_url, extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'investor':
            if hasattr(self, 'investor'):
                kwargs['queryset'] = self.investor
        return super(InvestAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

class CollectAdmin(admin.ModelAdmin):
    form = CollectForm
    list_display = ('id', 'project', 'user')
    fields = ('project', 'user')

    def save_model(self, request, obj, form, change):
        if change:
            if 'project' in form.changed_data or 'user' in form.changed_data:
                return messages.error(request, '✖ %s' %(Collect._meta.verbose_name.title()))
        obj.save()

class BannerAdmin(admin.ModelAdmin):
    form = BannerForm
    list_display = ('id', 'title', 'project', 'img', 'url')

class ThinktankAdmin(admin.ModelAdmin):
    form = ThinktankForm
    list_display = ('id', 'name', 'position', '_photo')
    def _photo(self, obj):
        #return '<a target="_blank" href="%s">img</a>' % (obj.photo.url)
        return  format_html('<img width="200px" src="%s"/>' % obj.photo.url)
    _photo.allow_tags = True
    _photo.short_description = '图像'

class NewsTypeAdmin(admin.ModelAdmin):
    form = NewsTypeForm
    list_display = ('id', 'name', 'eng', 'valid')
    list_editable = ('eng', 'valid')

class NewsAdmin(admin.ModelAdmin):
    form = NewsForm 
    list_display = ('id', 'title', '_create_datetime', '_url')
    def _create_datetime(self, obj):
        return dt_(obj.create_datetime)

    def _url(self, obj):
        return '%s/%s/%s/' % (settings.DOMAIN, 'phone/sanban', obj.name),

    _url.short_description = '网址'

class TopicAdmin(admin.ModelAdmin):
    form = TopicForm
    list_display = ('id', 'project', 'user', 'at_user', 'content', 'read')
    raw_id_fields = ('project', 'user', 'at')
    list_editable = ('read',)
    def at_user(self, obj):
        if obj.at:
            return obj.at.user.name
        return ''

class PushAdmin(admin.ModelAdmin):
    form = PushForm
    list_display = ('id', 'index', '_user', 'valid')
    raw_id_fields = ('user',)
    def _user(self, obj):
       return ','.join([user.tel for user in obj.user.all()]) 
    list_editable = ('valid',)

class InformAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'push', 'read')
    

class FeelingAdmin(admin.ModelAdmin):
    form = FeelingForm
    list_display = ('id', 'content', 'pic', 'create_datetime')
    raw_id_fields = ('user', 'like', )

class FeelingCommentAdmin(admin.ModelAdmin):
    form = FeelingCommentForm
    list_dispaly = ('id',)



