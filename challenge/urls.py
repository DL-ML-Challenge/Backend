from django.urls import path
from challenge import views

urlpatterns = [
    path('challenge/', views.ChallengeListAPIView.as_view()),
    path('challenge/<int:pk>/', views.ChallengeDetailAPIView.as_view()),
    path('phase/<int:pk>/', views.ChallengePhaseAPIView.as_view()),
    path('submit/<int:phase>/<int:group>/', views.GroupSubmitAPIView.as_view()),
    path('submit/<int:phase>/scoreboard', views.ScoreboardAPIView.as_view()),
]
