# coding: utf8
from django.contrib import admin
from .modeladmin import *
from django.utils.text import capfirst
#from django.utils.datastructures import SortedDict
from collections import OrderedDict

def find_model_index(name):
    count = 0
    for model, model_admin in admin.site._registry.items():
        if capfirst(model._meta.verbose_name_plural) == name:
            return count
        else:
            count += 1
    return count

def index_decorator(func):
    def inner(*args, **kwargs):
        templateresponse = func(*args, **kwargs)
        for app in templateresponse.context_data['app_list']:
            app['models'].sort(key = lambda x: find_model_index(x['name']))
        return templateresponse
    return inner

registry = OrderedDict()
registry.update(admin.site._registry)
admin.site._registry = registry
admin.site.index = index_decorator(admin.site.index)
admin.site.app_index = index_decorator(admin.site.app_index)

#admin.site.disable_action('delete_selected')
admin.site.register(Institute, InstituteAdmin)
admin.site.register(InvestCase, InvestCaseAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Upload, UploadAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Invest, InvestAdmin)
admin.site.register(Banner, BannerAdmin)
admin.site.register(Thinktank, ThinktankAdmin)
admin.site.register(NewsType)
admin.site.register(News, NewsAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Push, PushAdmin)
admin.site.register(Inform, InformAdmin)
admin.site.register(Feeling, FeelingAdmin)
admin.site.register(FeelingComment, FeelingCommentAdmin)
