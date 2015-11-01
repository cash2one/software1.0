# coding: utf-8
from django.forms import ValidationError
from django import forms

from .models import *

class QualificationForm(forms.ModelForm):
    class Meta:
        model = Qualification
        fields = '__all__'

class InstituteForm(forms.ModelForm):
    class Meta:
        model = Institute
        fields = '__all__'

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'
        

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = '__all__'

class UploadForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields = '__all__'

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super(ProjectForm, self).clean()
        planfinance = cleaned_data.get('planfinance')
        finance2get= cleaned_data.get('finance2get')
        share2give = cleaned_data.get('share2give')
        investor2plan = cleaned_data.get('investor2plan')
        investor2got = cleaned_data.get('investor2got')

        if planfinance and finance2get:
            if finance2get > planfinance:
                raise forms.ValidationError('%s > %s' %(Project._meta.get_field_by_name('finance2get')[0].verbose_name, Project._meta.get_field_by_name('planfinance')[0].verbose_name))

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


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = '__all__'

class InvestForm(forms.ModelForm):
    class Meta:
        model = Invest
        fields = '__all__'


class CollectForm(forms.ModelForm):
    class Meta:
        model = Collect
        fields = '__all__'

class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = '__all__'

class ThinktankForm(forms.ModelForm):
    class Meta:
        model = Thinktank
        fields = '__all__'

class VersionForm(forms.ModelForm):
    class Meta:
        model = Version
        fields = '__all__'

class NewsTypeForm(forms.ModelForm):
    class Meta:
        model = NewsType
        fields = '__all__'

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = '__all__'

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = '__all__'

class MsgTypeForm(forms.ModelForm):
    class Meta:
        model = MsgType
        fields = '__all__'

class PushForm(forms.ModelForm):
    class Meta:
        model = Push
        fields = '__all__'

class FeelingForm(forms.ModelForm):
    class Meta:
        model = Feeling
        fields = '__all__'

class FeelingCommentForm(forms.ModelForm):
    class Meta:
        model = FeelingComment
        fields = '__all__'
