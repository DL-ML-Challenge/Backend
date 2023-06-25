from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from groups.models import ChallengeUser


class ChallengeUserSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = ChallengeUser
        fields = ['id', 'full_name', 'student_code', 'group_name']


class ChallengeUserAPIView(APIView):
    def get(self, request):
        serializer = ChallengeUserSerializer(self.request.user.challenge_user)
        return Response(serializer.data)
