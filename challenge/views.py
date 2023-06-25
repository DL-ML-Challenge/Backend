import json
import random
import tempfile
from functools import cached_property

from django.conf import settings
from django.core.exceptions import BadRequest
from django.db.models import Max, Subquery, OuterRef, DecimalField
from django.http import Http404
from rest_framework import generics, mixins, status, serializers
from rest_framework.generics import ListCreateAPIView, get_object_or_404, ListAPIView, RetrieveAPIView
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from challenge import services
from challenge.authentication import JudgeSecretAuthentication
from challenge.models import Challenge, ChallengePhase, GroupSubmit
from challenge.permission import IsJudge
from challenge.serializers import (
    ChallengeSerializer, ChallengePhaseSerializer, GroupSubmitSerializer,
)
from groups.models import ChallengeGroup, ChallengeUser

import pika


# Create your views here.

class ChallengeDetailAPIView(
    mixins.RetrieveModelMixin,
    generics.GenericAPIView
):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class ChallengeListAPIView(
    mixins.ListModelMixin,
    generics.GenericAPIView
):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ChallengePhaseAPIView(
    mixins.RetrieveModelMixin,
    generics.GenericAPIView
):
    queryset = ChallengePhase.objects.all()
    serializer_class = ChallengePhaseSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


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
            submit = GroupSubmit.objects.create(
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


class GroupSubmitAPIView(APIView):
    parser_classes = (FileUploadParser,)

    def get(self, request, phase, group):
        try:
            phase = ChallengePhase.objects.get(pk=phase)
            group = ChallengeGroup.objects.get(pk=group)
        except (ChallengePhase.DoesNotExist, ChallengeGroup.DoesNotExist):
            raise Http404
        submits = GroupSubmit.objects.filter(group=group, phase=phase)
        serializer = GroupSubmitSerializer(submits, many=True)
        return Response(serializer.data)

    def post(self, request, phase, group, format='zip'):
        try:
            phase = ChallengePhase.objects.get(pk=phase)
            group = ChallengeGroup.objects.get(pk=group)
        except (ChallengePhase.DoesNotExist, ChallengeGroup.DoesNotExist):
            raise Http404
        up_file = request.FILES['file']
        rand = random.randint(1, 1000000)
        destination = open(
            f'{settings.MEDIA_ROOT}/{self.request.user.challenge_user.student_code}-{rand}.{format}',
            'wb+'
        )
        for chunk in up_file.chunks():
            destination.write(chunk)
        destination.close()
        submit = GroupSubmit(phase=phase, group=group, user=self.request.user.challenge_user, score=-1)
        submit.save()
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        if not client.bucket_exists("submit"):
            client.make_bucket("submit")
        client.fput_object(
            "submit", f'{self.request.user.challenge_user.student_code}/{submit.id}.{format}',
            f'{settings.MEDIA_ROOT}/{self.request.user.challenge_user.student_code}-{rand}.{format}'
        )
        credentials = pika.PlainCredentials(settings.RABBITMQ_USERNAME, settings.RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(settings.RABBITMQ_ENDPOINT, 5672, '/', credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.exchange_declare('challenge', exchange_type='fanout')
        channel.queue_declare(queue='submit')
        channel.queue_bind(exchange='challenge', queue='submit')
        channel.basic_publish(
            exchange='challenge',
            routing_key='',
            body=json.dumps(
                {
                    'phase': phase.name,
                    'tag': phase.tag,
                    'student_number': self.request.user.challenge_user.student_code,
                    'file_id': submit.id,
                }
            )
        )
        channel.close()
        return Response(GroupSubmitSerializer(submit), status.HTTP_201_CREATED)


class ScoreboardAPIView(APIView):
    def get(self, request, phase):
        try:
            phase = ChallengePhase.objects.get(pk=phase)
        except ChallengePhase.DoesNotExist:
            raise Http404
        submits = GroupSubmit.objects.filter(phase=phase).values('group').annotate(best_score=Max('score')).order_by(
            '-best_score'
        )
        return Response(GroupSubmitSerializer(submits, many=True), status.HTTP_200_OK)


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


class RejudgeAPIView(APIView):
    def get(self, request, phase, group):
        try:
            phase = ChallengePhase.objects.get(pk=phase)
            group = ChallengeGroup.objects.get(pk=group)
        except (ChallengePhase.DoesNotExist, ChallengeGroup.DoesNotExist):
            raise Http404
        submits = GroupSubmit.objects.filter(group=group, phase=phase).order_by('-created_at')[:10]
        credentials = pika.PlainCredentials(settings.RABBITMQ_USERNAME, settings.RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(settings.RABBITMQ_ENDPOINT, 5672, '/', credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.exchange_declare('challenge', exchange_type='fanout')
        channel.queue_declare(queue='submit')
        channel.queue_bind(exchange='challenge', queue='submit')
        for submit in submits:
            channel.basic_publish(
                exchange='challenge',
                routing_key='',
                body=json.dumps(
                    {
                        'phase': phase.name,
                        'tag': phase.tag,
                        'student_number': submit.user.student_code,
                        'file_id': submit.id,
                    }
                )
            )
        channel.close()
        return Response(GroupSubmitSerializer(submits, many=True), status.HTTP_200_OK)
