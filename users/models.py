from django.db import models
from django.contrib.auth.models import User


class AIUser(User):
    national_id = models.CharField(max_length=50, null=True, blank=True)
    student_number = models.CharField(max_length=10, null=True, blank=True)
