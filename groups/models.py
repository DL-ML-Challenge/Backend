from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class ChallengeGroup(models.Model):
    name = models.CharField(max_length=300)
    owner = models.OneToOneField('ChallengeUser', on_delete=models.SET_NULL, null=True, blank=True, default=None)


class ChallengeUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="challenge_user")
    full_name = models.CharField(max_length=300)
    student_code = models.CharField(max_length=9)
    group = models.ForeignKey(ChallengeGroup, on_delete=models.CASCADE, null=True, blank=True, default=None)
