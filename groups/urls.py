from django.urls import path
from groups import views

urlpatterns = [
    path('user/', views.ChallengeUserAPIView.as_view()),
    path('group/', views.ChallengeGroupListAPIView.as_view()),
    path('group/<int:pk>/', views.ChallengeGroupDetailAPIView.as_view()),
]
