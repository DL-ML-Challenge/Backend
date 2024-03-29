import random
import string

from django.db import models
from django.utils import timezone

from groups.models import ChallengeGroup


# Create your models here.

class Challenge(models.Model):
    name = models.CharField(max_length=200)


class ChallengePhase(models.Model):
    name = models.CharField(max_length=50)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField()

    def is_ongoing(self):
        return self.start <= timezone.now() <= self.end


def random_string(length=8):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


def get_submit_file_name(instance, filename):
    if filename and not filename.endswith(".zip") and "." in filename:
        extension = filename.rsplit(".", 1)[-1]
    else:
        extension = "zip"
    # return f"{instance.student_code}/{filename}-{random_string()}.zip"
    return f"{instance.student_code}/{random_string()}.{extension}"


class GroupSubmit(models.Model):
    phase = models.ForeignKey(ChallengePhase, on_delete=models.CASCADE)
    group = models.ForeignKey(ChallengeGroup, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to=get_submit_file_name)
    score = models.DecimalField(max_digits=50, decimal_places=20, null=True, blank=True)
    error = models.TextField(blank=True)

    @property
    def student_code(self):
        return self.group.challengeuser_set.first().student_code

    @property
    def is_judged(self):
        return len(self.error) > 0 or (self.score != -1 and self.score is not None)
