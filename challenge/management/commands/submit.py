import getpass
import tempfile

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS

from challenge import services
from challenge.models import Challenge, GroupSubmit

UserModel = get_user_model()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "student_code",
        )
        parser.add_argument(
            "challenge"
        )
        parser.add_argument(
            "drive_link",
        )

    def handle(self, *args, **options):
        student_code = options["student_code"]
        challenge_name = options["challenge"]
        drive_link = options["drive_link"]

        challenge = Challenge.objects.get(name=challenge_name)
        user = User.objects.get(username=student_code)
        phase = challenge.challengephase_set.first()

        with tempfile.NamedTemporaryFile() as tmp_file:
            downloaded = services.download_from_drive(tmp_file.name, url=drive_link)
            if not downloaded:
                raise CommandError("Could not download from this link")
            submit = GroupSubmit(
                phase=phase,
                group_id=user.challenge_user.group_id,
                score=-1,
            )
            with open(tmp_file.name, "rb") as f:
                submit.file.save("a.zip" if phase.challenge.name != "ml" else "a.ipynb", f, save=False)
            submit.save()
        services.send_submit_to_judge(submit)
