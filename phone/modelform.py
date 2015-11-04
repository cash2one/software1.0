# coding: utf-8
from django.forms import ValidationError
from django import forms

from .models import *

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
