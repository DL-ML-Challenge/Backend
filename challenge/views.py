import tempfile
from functools import cached_property

from django.core.exceptions import BadRequest
from django.db.models import Subquery, OuterRef, DecimalField
from django.http import Http404
from rest_framework import status, serializers
from rest_framework.generics import ListCreateAPIView, get_object_or_404, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from challenge import services
from challenge.authentication import JudgeSecretAuthentication
from challenge.models import ChallengePhase, GroupSubmit
from challenge.permission import IsJudge
from groups.models import ChallengeGroup, ChallengeUser


class ListCreateGroupSubmitAPIView(ListCreateAPIView):
    class GroupSubmitSerializer(serializers.ModelSerializer):
        class Meta:
            model = GroupSubmit
            fields = [
                "file",
                "score",
                "created_at",
                "is_judged",
                "error",
            ]
            extra_kwargs = {
                "file": {"write_only": True},
                "score": {"read_only": True},
                "created_at": {"read_only": True},
                "error": {"read_only": True},
            }

    serializer_class = GroupSubmitSerializer

    @cached_property
    def phase(self):
        return get_object_or_404(
            ChallengePhase,
            name=self.kwargs["phase_name"],
            challenge__name=self.kwargs["challenge_name"],
        )

    def get_queryset(self):
        return GroupSubmit.objects.filter(
            group_id=self.request.user.challenge_user.group_id,
            phase=self.phase
        ).order_by("-id")

    def perform_create(self, serializer):
        submit = serializer.save(phase=self.phase, group_id=self.request.user.challenge_user.group_id, score=-1)
        services.send_submit_to_judge(submit)


class CreateGoogleDriveGroupSubmitAPIView(ListCreateAPIView):
    class GroupSubmitSerializer(serializers.ModelSerializer):
        url = serializers.URLField()

        class Meta:
            model = GroupSubmit
            fields = [
                "url",
            ]

    serializer_class = GroupSubmitSerializer

    @cached_property
    def phase(self):
        return get_object_or_404(
            ChallengePhase,
            name=self.kwargs["phase_name"],
            challenge__name=self.kwargs["challenge_name"],
        )

    def get_queryset(self):
        return GroupSubmit.objects.filter(
            group_id=self.request.user.challenge_user.group_id,
            phase=self.phase
        ).order_by("-id")

    def perform_create(self, serializer):
        with tempfile.NamedTemporaryFile() as tmp_file:
            downloaded = services.download_from_drive(tmp_file.name, url=serializer.validated_data["url"])
            if not downloaded:
                raise BadRequest("Could not download from this link")
            submit = GroupSubmit(
                phase=self.phase,
                group_id=self.request.user.challenge_user.group_id,
                score=-1,
            )
            with open(tmp_file.name, "rb") as f:
                submit.file.save("a.zip" if self.phase.challenge.name != "ml" else "a.ipynb", f, save=False)
            submit.save()
        services.send_submit_to_judge(submit)


class RankingGroupUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeUser
        fields = [
            "full_name",
        ]


class RankingAPIView(ListAPIView):
    class RankingGroupSerializer(serializers.ModelSerializer):
        best_score = serializers.DecimalField(max_digits=50, decimal_places=20)
        users = RankingGroupUserSerializer(source="challengeuser_set", many=True)

        class Meta:
            model = ChallengeGroup
            fields = [
                "best_score",
                "name",
                "users",
            ]

    permission_classes = [IsAuthenticated]
    serializer_class = RankingGroupSerializer

    @cached_property
    def phase(self):
        return get_object_or_404(
            ChallengePhase,
            name=self.kwargs["phase_name"],
            challenge__name=self.kwargs["challenge_name"],
        )

    def get_queryset(self):
        return ChallengeGroup.objects.annotate(
            best_score=Subquery(
                GroupSubmit.objects.filter(
                    phase=self.phase,
                    group_id=OuterRef("id"),
                    score__isnull=False,
                ).exclude(score=-1).order_by("-score").values("score")[:1],
                output_field=DecimalField(max_digits=50, decimal_places=20)
            ),
        ).filter(best_score__isnull=False).order_by("-best_score")


class ScoreSubmitAPIView(APIView):
    authentication_classes = [JudgeSecretAuthentication]
    permission_classes = [IsJudge]

    def get(self, request, student_code, file_id):
        try:
            submit = GroupSubmit.objects.get(pk=file_id)
        except GroupSubmit.DoesNotExist:
            raise Http404
        return Response({"is_judged": submit.is_judged}, status.HTTP_200_OK)

    def post(self, request, student_code, file_id):
        try:
            submit = GroupSubmit.objects.get(pk=file_id)
        except GroupSubmit.DoesNotExist:
            raise Http404
        submit.score = request.data.get("score", -1)
        submit.error = request.data.get("error", "")
        submit.save()
        return Response({}, status.HTTP_200_OK)
