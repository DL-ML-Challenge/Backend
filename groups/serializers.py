from rest_framework import serializers

from groups.models import ChallengeUser, ChallengeGroup


class ChallengeUserSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = ChallengeUser
        fields = ['id', 'full_name', 'student_code', 'group_name']


class ChallengeGroupSerializer(serializers.ModelSerializer):
    challengeuser_set = ChallengeUserSerializer(read_only=True, many=True)

    class Meta:
        model = ChallengeGroup
        fields = ['id', 'name', 'challengeuser_set']
