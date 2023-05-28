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
        destination = open(settings.MEDIA_ROOT + '/' + up_file.name, 'wb+')
        for chunk in up_file.chunks():
            destination.write(chunk)
        destination.close()
        # TODO: judge the uploaded file
        submit = GroupSubmit(phase=phase, group=group, score=100).save()
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
