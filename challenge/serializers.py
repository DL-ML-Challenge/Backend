from rest_framework import serializers

from challenge.models import Challenge, ChallengePhase, GroupParticipation, GroupSubmit


# Create your models here.

class GroupParticipationSerializer(serializers.ModelSerializer):
    group_name = serializers.RelatedField(source='group.name', read_only=True)

    class Meta:
        model = GroupParticipation
        fields = ['group_name']


class ChallengePhaseSerializer(serializers.ModelSerializer):
    groupparticipation_set = GroupParticipationSerializer(read_only=True, many=True)

    class Meta:
        model = ChallengePhase
        fields = ['id', 'name']


class ChallengeSerializer(serializers.ModelSerializer):
    challengephase_set = ChallengePhaseSerializer(read_only=True, many=True)

    class Meta:
        model = Challenge
        fields = ['id', 'name', 'challengephase_set']


class GroupSubmitSerializer(serializers.ModelSerializer):
    group_name = serializers.RelatedField(source='group.name', read_only=True)
    phase_challenge_name = serializers.RelatedField(source='phase.challenge.name', read_only=True)

    class Meta:
        model = GroupSubmit
        fields = ['id', 'group_name', 'phase_challenge_name', 'score']
