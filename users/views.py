from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import re
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import AIUser


@api_view(['POST'])
def register(request):
    email = request.data.get('email')
    national_id = request.data.get('notional_id')
    student_number = request.data.get('student_number')
    user = AIUser.objects.create_user(email=email, national_id=national_id, student_number=student_number)
    user.save()

    refresh = RefreshToken.for_user(user)

    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def login(request):
    stn_or_email = request.data.get('id')
    print(f'agbr {stn_or_email}')
    national_id = request.data.get('notional_id')
    if re.match(r"[^@]+@[^@]+\.[^@]+", stn_or_email):
        user = AIUser.objects.filter(email=stn_or_email, national_id=national_id).first()
    elif re.match(r"^[0-9]*$", stn_or_email):
        user = AIUser.objects.filter(student_number=stn_or_email, national_id=national_id).first()
    else:
        return Response({'message': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)
    if not user:
        return Response({'error': 'Invalid information'}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)

    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=status.HTTP_200_OK)
