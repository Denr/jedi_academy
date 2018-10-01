from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Count
from django.http import (HttpResponse, Http404)
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import (reverse_lazy, reverse)
from django.views.generic import (TemplateView, FormView, CreateView, ListView, DetailView)

from jedi_academy.settings import EMAIL_HOST_USER
from main.forms import (CandidateForm, AnswerForm, JediSelectForm)
from main.models import (Candidate, Question, Challenge, Answer, Jedi)


class IndexView(TemplateView):
    template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        self.request.session.flush()
        return render(request, self.template_name)


class CreateCandidate(CreateView):
    template_name = 'create_candidate.html'
    form_class = CandidateForm

    def form_valid(self, form):
        try:
            return super(CreateCandidate, self).form_valid(form)
        except ValidationError:
            return HttpResponse('К сожалению в данный момент мы не можем Вас принять.'
                                'У Джедая с Вашей планеты уже больше 3 падаванов.')

    def get_success_url(self):
        self.request.session['candidate_id'] = self.object.pk
        # Показываем первый вопрос с кодом ордена 123
        # из тз не понял как орден влияет на вопросы, поэтому решил оставить так
        return reverse('challenge', kwargs={'order': 123, 'question': 1})


class ChallengeView(FormView):
    template_name = 'challenge.html'
    form_class = AnswerForm

    def get(self, request, *args, **kwargs):
        # Если кандидат не зарегистрировался показываем ему 403
        if request.session.get('candidate_id') is None:
            return HttpResponse(status=403)
        return super(ChallengeView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        session = self.request.session
        session['question_' + str(self.kwargs['question'])] = form.cleaned_data['answer_text']
        return super(ChallengeView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(ChallengeView, self).get_form_kwargs()
        kwargs['question_pk'] = self.kwargs['question']
        kwargs['order_code'] = self.kwargs['order']
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ChallengeView, self).get_context_data(**kwargs)
        try:
            context['question'] = Challenge.objects.get(order__code=self.kwargs.get('order')).questions.get(
                pk=self.kwargs.get('question'))
        except (Challenge.DoesNotExist, Question.DoesNotExist):
            raise Http404()
        return context

    def get_success_url(self, **kwargs):
        next_question = Challenge.challenge_manager.get_next_question(order_code=self.kwargs.get('order'),
                                                                      question_pk=self.kwargs.get('question'))
        if next_question != 'done':
            return reverse_lazy('challenge', kwargs={'order': self.kwargs.get('order'), 'question': next_question})
        else:
            self.save_answers()
            self.request.session.flush()
            return reverse('complete_challenge')

    def save_answers(self):
        candidate_id = self.request.session.get('candidate_id')
        candidate = get_object_or_404(Candidate, pk=candidate_id)
        questions = get_object_or_404(Challenge, order__code=self.kwargs.get('order')).questions.all()
        for i, question in enumerate(questions):
            answer_text = self.request.session.get('question_' + str(i + 1))
            try:
                Answer.objects.create(question=question, answer_text=answer_text, candidate=candidate)
            # На всякий случай проверяем что такой кандидат не отвечает на вопросы повторно
            except IntegrityError:
                return HttpResponse(status=403)


class CompleteChallengeView(TemplateView):
    template_name = 'complete_challenge.html'


class SelectJediView(FormView):
    form_class = JediSelectForm
    template_name = 'select_jedi.html'
    success_url = reverse_lazy('candidate_list')

    def form_valid(self, form):
        self.request.session['jedi_id'] = form.cleaned_data['jedi'].id
        return super(SelectJediView, self).form_valid(form)


class CandidateListView(ListView):
    template_name = 'candidate_list.html'
    paginate_by = 10
    context_object_name = 'candidate_list'

    def get(self, request, *args, **kwargs):
        if self.request.session.get('jedi_id') is None:
            return HttpResponse(status=403)
        return super(CandidateListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        jedi_id = self.request.session.get('jedi_id')
        jedi = get_object_or_404(Jedi, pk=jedi_id)
        # Выбираем кандидатов с планеты Джедая которые еще не стали падаванами
        return Candidate.objects.filter(planet=jedi.planet, jedi=None)


class CandidateAnswerView(DetailView):
    template_name = 'candidate_answer.html'
    model = Candidate
    pk_url_kwarg = 'candidate'

    # Не даем Джедаем смотреть кандидатов не с их планеты
    def check_permission(self, jedi, candidate):
        if jedi.planet.pk != candidate.planet.pk:
            return HttpResponse(status=403)

    def get_context_data(self, **kwargs):
        context = super(CandidateAnswerView, self).get_context_data(**kwargs)
        context['jedi'] = get_object_or_404(Jedi, pk=self.request.session.get('jedi_id'))
        return context

    def get(self, request, *args, **kwargs):
        jedi = get_object_or_404(Jedi, pk=self.request.session.get('jedi_id'))
        candidate = get_object_or_404(Candidate, pk=kwargs.get('candidate'), jedi=None)
        self.check_permission(jedi, candidate)
        return super(CandidateAnswerView, self).get(request, *args, **kwargs)

    def post(self, *args, **kwargs):
        jedi = get_object_or_404(Jedi, pk=self.request.session.get('jedi_id'))
        candidate = get_object_or_404(Candidate, pk=kwargs.get('candidate'), jedi=None)
        self.check_permission(jedi, candidate)
        if jedi.candidates.count() >= 3:
            return HttpResponse('У Вас и так уже 3 падавана. Пока Вы не можете взять себе новых падаванов.', status=403)
        send_mail(subject='Поздравляем!'.format(candidate.name),
                  message='{}, Вы были зачислены в падаваны к Джедаю {}!'.format(candidate.name, jedi.name),
                  from_email=EMAIL_HOST_USER, recipient_list=[candidate.email])
        candidate.jedi = jedi
        candidate.save()
        return render(self.request, 'padawan_accepted.html', context={'candidate': candidate})


class JediWithPadawansView(ListView):
    template_name = 'jedi_list.html'
    paginate_by = 10
    context_object_name = 'jedi_list'

    def get_queryset(self):
        return Jedi.objects.annotate(padawans_count=Count('candidates'))


class JediWithMoreOnePadawanView(ListView):
    template_name = 'jedi_list.html'
    paginate_by = 10
    context_object_name = 'jedi_list'

    def get_queryset(self):
        return Jedi.objects.annotate(padawans_count=Count('candidates')).filter(padawans_count__gt=1)
