from django.db import models
from groups.models import ChallengeGroup


# Create your models here.

class Challenge(models.Model):
    name = models.CharField(max_length=200)


class ChallengePhase(models.Model):
    name = models.CharField(max_length=50)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)


class GroupParticipation(models.Model):
    phase = models.ForeignKey(ChallengePhase, on_delete=models.CASCADE)
    group = models.ForeignKey(ChallengeGroup, on_delete=models.CASCADE)


class GroupSubmit(models.Model):
    phase = models.ForeignKey(ChallengePhase, on_delete=models.CASCADE)
    group = models.ForeignKey(ChallengeGroup, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=50, decimal_places=20)
