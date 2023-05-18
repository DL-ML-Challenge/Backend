from django.http import Http404
from django.shortcuts import render
from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework.views import APIView

from groups.models import ChallengeUser, ChallengeGroup
from groups.serializers import ChallengeUserSerializer, ChallengeGroupSerializer


# Create your views here.

class ChallengeUserAPIView(APIView):

    def get(self, request, student_code):
        try:
            user = ChallengeUser.objects.get(student_code=student_code)
        except ChallengeUser.DoesNotExist:
            raise Http404
        serializer = ChallengeUserSerializer(user)
        return Response(serializer.data)


class ChallengeGroupDetailAPIView(mixins.RetrieveModelMixin,
                                  generics.GenericAPIView):
    queryset = ChallengeGroup.objects.all()
    serializer_class = ChallengeGroupSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class ChallengeGroupListAPIView(mixins.ListModelMixin,
                                generics.GenericAPIView):
    queryset = ChallengeGroup.objects.all()
    serializer_class = ChallengeGroupSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
