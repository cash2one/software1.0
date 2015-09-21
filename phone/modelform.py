# coding: utf-8
from django.forms import ValidationError
from django import forms

from .models import *

class QualificationForm(forms.ModelForm):
    class Meta:
        model = Qualification
        fields = '__all__'

class FundSizeRangeForm(forms.ModelForm):
    class Meta:
        model = FundSizeRange
        fields = '__all__'

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'

class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = '__all__'

class JoinShipForm(forms.ModelForm):
    class Meta:
        model = JoinShip
        fields = '__all__'

class CompanystatusForm(forms.ModelForm):
    class Meta:
        model = Companystatus
        fields = '__all__'

class IndustryForm(forms.ModelForm):
    class Meta:
        model = Industry
        fields = '__all__'
        
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = '__all__'

class RoadshowForm(forms.ModelForm):
    class Meta:
        model = Roadshow
        fields = '__all__'

    def clean(self):
        cleaned_data = super(RoadshowForm, self).clean()
        if self.instance: #更改
            roadshow_datetime = cleaned_data.get('roadshow_datetime')
            if roadshow_datetime:
                create_datetime = self.instance.create_datetime
                if roadshow_datetime < create_datetime: 
                    create_datetime = timeformat(self.instance.create_datetime)
                    raise ValidationError('路演时间必须 < %s' % create_datetime)

class InvestorForm(forms.ModelForm):
    class Meta:
        model = Investor
        fields = '__all__'

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super(ProjectForm, self).clean()
        planfinance = cleaned_data.get('planfinance')
        already_finance = cleaned_data.get('already_finance')
        share2give = cleaned_data.get('share2give')
        investor2plan = cleaned_data.get('investor2plan')
        investor2got = cleaned_data.get('investor2got')

        if planfinance and already_finance:
            if already_finance > planfinance:
                raise forms.ValidationError('%s > %s' %(Project._meta.get_field_by_name('already_finance')[0].verbose_name, Project._meta.get_field_by_name('planfinance')[0].verbose_name))

        if investor2plan and investor2got:
            if investor2got > investor2plan:
                raise ValidationError('%s > %s' %(Project._meta.get_field_by_name('investor2got')[0].verbose_name, Project._meta.get_field_by_name('investor2plan')[0].verbose_name))

        roadshow_start_datetime = cleaned_data.get('roadshow_start_datetime')
        roadshow_stop_datetime = cleaned_data.get('roadshow_stop_datetime')
        finance_stop_datetime = cleaned_data.get('finance_stop_datetime')

        if roadshow_start_datetime and roadshow_stop_datetime and finance_stop_datetime:
            if roadshow_start_datetime >= roadshow_stop_datetime:
                raise forms.ValidationError('路演开始时间 必须< 路演截至时间')
            elif roadshow_stop_datetime > finance_stop_datetime:
                raise forms.ValidationError('路演截至时间 必须<= 融资截至时间')

class ProjectEventForm(forms.ModelForm):
    class Meta:
        model = ProjectEvent
        fields = '__all__'

class CoreMemberForm(forms.ModelForm):
    class Meta:
        model = CoreMember
        fields = '__all__'

class ParticipateShipForm(forms.ModelForm):
    class Meta:
        model = ParticipateShip
        fields = '__all__'

class InvestShipForm(forms.ModelForm):
    class Meta:
        model = InvestShip
        fields = '__all__'

class VoteShipForm(forms.ModelForm):
    class Meta:
        model = VoteShip
        fields = '__all__'

class LikeShipForm(forms.ModelForm):
    class Meta:
        model = LikeShip
        fields = '__all__'

class CollectShipForm(forms.ModelForm):
    class Meta:
        model = CollectShip
        fields = '__all__'

class RecommendProjectForm(forms.ModelForm):
    class Meta:
        model = RecommendProject
        fields = '__all__'
        
class BannerTypeForm(forms.ModelForm):
    class Meta:
        model = BannerType
        fields = '__all__'

class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = '__all__'

class ThinktankForm(forms.ModelForm):
    class Meta:
        model = Thinktank
        fields = '__all__'

class ThinktankCollectForm(forms.ModelForm):
    class Meta:
        model = ThinktankCollect
        fields = '__all__'

class SystemForm(forms.ModelForm):
    class Meta:
        model = System
        fields = '__all__'

class VersionForm(forms.ModelForm):
    class Meta:
        model = Version
        fields = '__all__'

class InformlistForm(forms.ModelForm):
    class Meta:
        model = Informlist
        fields = '__all__'

class BlacklistForm(forms.ModelForm):
    class Meta:
        model = Blacklist
        fields = '__all__'

class SigninForm(forms.ModelForm):
    class Meta:
        model = Signin
        fields = '__all__'

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = '__all__'

    def clean(self):
        cleaned_data = super(ActivityForm, self).clean()
        start_datetime = cleaned_data.get('start_datetime')
        stop_datetime = cleaned_data.get('stop_datetime')
        if start_datetime and stop_datetime:
            datetime_format = '%Y-%m-%d %H:%M:%S'
            import pytz
            utc = pytz.UTC
            if start_datetime  < utc.localize( datetime.now() - timedelta(days=2) ):
                raise ValidationError('活动必须提前两天登记')

            if start_datetime >= stop_datetime:
                raise ValidationError('结束时间必须晚于开始时间')

class NewsTypeForm(forms.ModelForm):
    class Meta:
        model = NewsType
        fields = '__all__'

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = '__all__'

class KnowledgeTypeForm(forms.ModelForm):
    class Meta:
        model = KnowledgeType
        fields = '__all__'

class KnowledgeForm(forms.ModelForm):
    class Meta:
        model = Knowledge
        fields = '__all__'

class KeywordForm(forms.ModelForm):
    class Meta:
        model = Keyword
        fields = '__all__'

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = '__all__'

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = '__all__'

class AboutusForm(forms.ModelForm):
    class Meta:
        model = Aboutus
        fields = '__all__'

class MsgTypeForm(forms.ModelForm):
    class Meta:
        model = MsgType
        fields = '__all__'

class PushForm(forms.ModelForm):
    class Meta:
        model = Push
        fields = '__all__'

class MsgreadForm(forms.ModelForm):
    class Meta:
        model = Msgread
        fields = '__all__'
