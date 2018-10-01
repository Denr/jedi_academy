from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from main.models import (Candidate, Answer, Jedi)


class CandidateForm(ModelForm):
    class Meta:
        model = Candidate
        exclude = ['jedi']
        labels = {'name': _('Имя'), 'planet': _('Планета вашего обитания'), 'age': _('Возраст'), 'email': _('E-mail')}

    def __init__(self, *args, **kwargs):
        super(CandidateForm, self).__init__(*args, **kwargs)
        self.fields['age'].widget.attrs['min'] = 20
        self.fields['age'].widget.attrs['max'] = 100


class AnswerForm(ModelForm):
    answer_text = forms.CharField(widget=forms.RadioSelect(choices=((True, _('Да'),), (False, _('Нет')),)),
                                  label='Ответ')

    class Meta:
        model = Answer
        fields = ['answer_text']

    def __init__(self, order_code, question_pk, *args, **kwargs):
        self.order_code = order_code
        self.question_id = question_pk
        super(AnswerForm, self).__init__(*args, **kwargs)


class JediSelectForm(forms.Form):
    jedi = forms.ModelChoiceField(queryset=Jedi.objects.all(), label='Выберите себя из списка')
