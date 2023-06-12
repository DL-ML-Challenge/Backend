from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header


class JudgeSecretAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = get_authorization_header(request).decode()
        if auth == settings.JUDGE_SECRET:
            request.is_judge = True
        return None
