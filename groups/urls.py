from django.urls import path
from groups import views

urlpatterns = [
    path('user/', views.ChallengeUserAPIView.as_view()),
]
