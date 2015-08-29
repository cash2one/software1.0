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

#registry = SortedDict()
registry = OrderedDict()
registry.update(admin.site._registry)
admin.site._registry = registry
admin.site.index = index_decorator(admin.site.index)
admin.site.app_index = index_decorator(admin.site.app_index)

admin.site.disable_action('delete_selected')
admin.site.register(Qualification, QualificationAdmin)
admin.site.register(FundSizeRange, FundSizeRangeAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(JoinShip, JoinShipAdmin)
admin.site.register(Companystatus, CompanystatusAdmin)
admin.site.register(Industry, IndustryAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Roadshow, RoadshowAdmin)
admin.site.register(Investor, InvestorAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectEvent, ProjectEventAdmin)
admin.site.register(CoreMember, CoreMemberAdmin)
admin.site.register(ParticipateShip, ParticipateShipAdmin)
admin.site.register(InvestShip, InvestShipAdmin)
admin.site.register(LikeShip, LikeShipAdmin)
admin.site.register(CollectShip, CollectShipAdmin)
admin.site.register(BannerType, BannerTypeAdmin)    
admin.site.register(RecommendProject, RecommendProjectAdmin)
admin.site.register(Banner, BannerAdmin)
admin.site.register(Thinktank, ThinktankAdmin)
admin.site.register(ThinktankCollect, ThinktankCollectAdmin)    
admin.site.register(System, SystemAdmin)
admin.site.register(Version, VersionAdmin)
#admin.site.register(Informlist, InformlistAdmin)
#admin.site.register(Blacklist, BlacklistAdmin)
admin.site.register(Activity, ActivityAdmin)
admin.site.register(Signin, SigninAdmin)
#admin.site.register(NewsType, NewsTypeAdmin)
#admin.site.register(News, NewsAdmin)
#admin.site.register(KnowledgeType, KnowledgeTypeAdmin)
#admin.site.register(Knowledge, KnowledgeAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Aboutus, AboutusAdmin)
admin.site.register(Feedback, FeedbackAdmin)
