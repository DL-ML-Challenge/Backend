from django.db import models
from groups.models import ChallengeGroup, ChallengeUser


# Create your models here.

class Challenge(models.Model):
    name = models.CharField(max_length=200)


class ChallengePhase(models.Model):
    name = models.CharField(max_length=50)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    tag = models.CharField(max_length=20, default='vision')


class GroupParticipation(models.Model):
    phase = models.ForeignKey(ChallengePhase, on_delete=models.CASCADE)
    group = models.ForeignKey(ChallengeGroup, on_delete=models.CASCADE)


class GroupSubmit(models.Model):
    phase = models.ForeignKey(ChallengePhase, on_delete=models.CASCADE)
    group = models.ForeignKey(ChallengeGroup, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(ChallengeUser, null=True, on_delete=models.SET_NULL)
    file = models.FileField()
    score = models.DecimalField(max_digits=50, decimal_places=20, null=True, blank=True)
