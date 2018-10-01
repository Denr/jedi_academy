from django.urls import path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('new_candidate/', views.CreateCandidate.as_view(), name='create_candidate'),
    path('challenge/order_<int:order>_<int:question>/', views.ChallengeView.as_view(), name='challenge'),
    path('challenge/done/', views.CompleteChallengeView.as_view(), name='complete_challenge'),
    path('jedi/', views.SelectJediView.as_view(), name='select_jedi'),
    path('jedi/candidates/', views.CandidateListView.as_view(), name='candidate_list'),
    path('jedi/candidate_<int:candidate>_answer/', views.CandidateAnswerView.as_view(), name='candidate_answer'),
    path('jedi/all/', views.JediWithPadawansView.as_view(), name='jedi_list_all'),
    path('jedi/more_one/', views.JediWithMoreOnePadawanView.as_view(), name='jedi_list_more_one')

]
