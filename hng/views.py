from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Organisation
from .serializers import UserSerializer, OrganisationSerializer, AddUserSerializer
from .permissions import IsMember

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            payload = {
                'status': 'success',
                'message': 'Login successful',
                'data': serializer.data
            }
        except Exception as e:
            payload = {
                'status': 'Bad request',
                'message': 'Authentication failed',
                'statusCode': status.HTTP_401_UNAUTHORIZED
            }
            return Response(payload, status=status.HTTP_401_UNAUTHORIZED)

        return Response(payload, status=status.HTTP_200_OK)


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'userId'
    # lookup_url_kwarg = 'userId'

    def get_permissions(self):
        if self.action == 'retrieve':
            permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            payload = {
                'status': 'success',
                'message': 'Registration successful',
                'data': {
                    'accessToken': access_token,
                    # 'user': serializer.data,
                    'user': {
                        'userId': serializer.data['userId'],
                        'firstName': serializer.data['firstName'],
                        'lastName': serializer.data['lastName'],
                        'email': serializer.data['email'],
                        'phone': serializer.data['phone'],
                    }
                }
            }
            return Response(payload, status=status.HTTP_201_CREATED, headers=headers)
        
        except ValidationError as error:
            errors = error.detail
            formatted_errors = []

            for field, error_details in errors.items():
                error_detail = error_details[0]
                formatted_error = {
                    'field': field,
                    'message': error_detail
                }
                formatted_errors.append(formatted_error)

            payload = {'errors': formatted_errors}
            return Response(payload, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        except Exception as e:
            payload = {
                'status': 'Bad request',
                'message': 'Registration unsuccessful',
                'statusCode': status.HTTP_400_BAD_REQUEST
            }
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_create(self, serializer):
        return serializer.save()
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        payload = {
            'status': 'success',
            'message': 'User successfully retrieved',
            # 'data': response.data,
            'data': {
                'userId': response.data['userId'],
                'firstName': response.data['firstName'],
                'lastName': response.data['lastName'],
                'email': response.data['email'],
                'phone': response.data['phone'],
            }
        }
        return Response(payload, status=status.HTTP_200_OK)


class OrganisationViewSet(mixins.CreateModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.ListModelMixin,
                          viewsets.GenericViewSet):

    queryset = Organisation.objects.all()
    serializer_class = OrganisationSerializer
    lookup_field = 'orgId'
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return self.queryset.filter(users__in=[user])
        else:
            return Organization.objects.none()
    
    def get_permissions(self):
        if self.action == 'retrieve':
            permission_classes = [IsMember]
        elif self.action == 'add_user':
            permission_classes = [AllowAny]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'add_user':
            return AddUserSerializer
        return super().get_serializer_class()
    
    def create(self, request, *args, **kwargs):
        try:
            reponse = super().create(request, *args, **kwargs)
            if response:
                payload = {
                    'status': 'success',
                    'message': 'Organisation created successfully',
                    'data': reponse.data
                }
                return Response(payload, status=status.HTTP_201_CREATED)

        except ValidationError as error:
            errors = error.detail
            formatted_errors = []

            for field, error_details in errors.items():
                error_detail = error_details[0]
                formatted_error = {
                    'field': field,
                    'message': error_detail
                }
                formatted_errors.append(formatted_error)

            payload = {'errors': formatted_errors}
            return Response(payload, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            payload = {
                'status': 'Bad request',
                'message': 'Client error',
                'statusCode': status.HTTP_400_BAD_REQUEST
            }
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        payload = {
            'status': 'success',
            'message': 'Organisation successfully retrieved',
            'data': response.data
        }
        return Response(payload, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        payload = {
            'status': 'success',
            'message': 'Organisations in which you are a member of, sucessfully retrieved',
            'data': response.data
        }
        return Response(payload, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"],url_path="users")
    def add_user(self, request, *args, **kwargs):
        organisation = self.get_object()

        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                user_id = serializer.data
                user = get_object_or_404(User, userId=user_id['userId'])
                if user in organisation.users.all():
                    payload = {
                        'status': 'success',
                        'message': 'User already added to organisation'
                    }
                else:
                    organisation.users.add(user)
                    payload = {
                        'status': 'success',
                        'message': 'User added to organisation successfully'
                    }
                return Response(payload, status=status.HTTP_200_OK)
        except:
            payload = {
                'status': 'Bad request',
                'message': 'Client error',
                'statusCode': status.HTTP_400_BAD_REQUEST
            }
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

