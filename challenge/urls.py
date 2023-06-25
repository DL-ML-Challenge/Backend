from django.urls import path
from challenge import views

urlpatterns = [
    path('<str:challenge_name>/<str:phase_name>/submit/', views.ListCreateGroupSubmitAPIView.as_view()),
    path('<str:challenge_name>/<str:phase_name>/submit-drive/', views.CreateGoogleDriveGroupSubmitAPIView.as_view()),
    path('<str:challenge_name>/<int:phase_name>/ranking/', views.RankingAPIView.as_view()),
    path('submit/<int:student_code>/<int:file_id>/score', views.ScoreSubmitAPIView.as_view()),
]
