import json
import random
from functools import cached_property

from django.conf import settings
from django.db.models import Max
from django.http import Http404
from rest_framework import generics, mixins, status, serializers
from rest_framework.generics import ListCreateAPIView, get_object_or_404
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView

from challenge.models import Challenge, ChallengePhase, GroupSubmit
from challenge.serializers import (
    ChallengeSerializer, ChallengePhaseSerializer, GroupSubmitSerializer,
)
from groups.models import ChallengeGroup

from minio import Minio
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
            ]
            extra_kwargs = {
                "file": {"write_only": True},
                "score": {"read_only": True},
                "created_at": {"read_only": True},
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
        serializer.save(phase=self.phase, group_id=self.request.user.challenge_user.group_id)


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
        destination = open(f'{settings.MEDIA_ROOT}/{self.request.user.challenge_user.student_code}-{rand}.{format}',
                           'wb+')
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
        channel.basic_publish(exchange='challenge',
                              routing_key='',
                              body=json.dumps({
                                  'phase': phase.name,
                                  'tag': phase.tag,
                                  'student_number': self.request.user.challenge_user.student_code,
                                  'file_id': submit.id,
                              }))
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

    def get(self, request, student_code, file_id):
        try:
            submit = GroupSubmit.objects.get(pk=file_id)
        except GroupSubmit.DoesNotExist:
            raise Http404
        if not submit.group.challengeuser_set.objects.filter(student_code=student_code).exists():
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(f'{submit.score != -1}', status.HTTP_200_OK)

    def post(self, request, student_code, file_id):
        try:
            submit = GroupSubmit.objects.get(pk=file_id)
        except GroupSubmit.DoesNotExist:
            raise Http404
        if not submit.group.challengeuser_set.objects.filter(student_code=student_code).exists():
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        submit.score = request.POST.get('score', -1)
        submit.save()
        return Response(GroupSubmitSerializer(submit), status.HTTP_200_OK)


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
            channel.basic_publish(exchange='challenge',
                                  routing_key='',
                                  body=json.dumps({
                                      'phase': phase.name,
                                      'tag': phase.tag,
                                      'student_number': submit.user.student_code,
                                      'file_id': submit.id,
                                  }))
        channel.close()
        return Response(GroupSubmitSerializer(submits, many=True), status.HTTP_200_OK)
