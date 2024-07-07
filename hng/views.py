from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .serializers import UserSerializer

User = get_user_model()



@api_view(['POST'])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token = Token.objects.create(user=user)
        payload = {
            'status': 'success',
            'message': 'Registration successful',
            'data': {
                'accessToken': token.key,
                'user': serializer.data
            }
        }
        return Response(payload, status=status.HTTP_201_CREATED)
    # else:
    #     print(serializer.errors)
    

    payload = {
        'status': 'Bad request',
        'message': 'Registration unsuccessful',
        'statusCode': status.HTTP_400_BAD_REQUEST
    }
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login(request):
    user = get_object_or_404(User, email=request.data['email'])
    if not user.check_password(request.data['password']):
        payload = {
            'status': 'Bad request',
            'message': 'Authentication failed',
            'statusCode': status.HTTP_401_UNAUTHORIZED
        }
        return Response(payload, status=status.HTTP_401_UNAUTHORIZED)

    token, created = Token.objects.get_or_create(user=user)
    serializer = UserSerializer(user)
    payload = {
        'status': 'success',
        'message': 'Login successful',
        'data': {
            'accessToken': token.key,
            'user': serializer.data
        }
    }
    return Response(payload, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def test_token(request):
    return Response("passed!")


