from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

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
                'data': serializer.validated_data
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
        instance = self.get_object()
        if instance.userId != request.user.userId:
            # Check for shared organisation membership if requesting different user
            shared_orgs = instance.organisation_set.filter(users=request.user)
            if not shared_orgs.exists():
                payload = {
                    'status': 'Unauthorized',
                    'message': 'You do not have the permission to retrieve this user',
                    'statusCode': status.HTTP_403_FORBIDDEN
                }
                return Response(payload, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance)
        payload = {
            'status': 'success',
            'message': 'User successfully retrieved',
            # 'data': serializer.data,
            'data': {
                'userId': serializer.data['userId'],
                'firstName': serializer.data['firstName'],
                'lastName': serializer.data['lastName'],
                'email': serializer.data['email'],
                'phone': serializer.data['phone'],
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
        if self.action == 'list':
            user = self.request.user
            return self.queryset.filter(users__in=[user])
        return super().get_queryset()
    
    def get_permissions(self):
        if self.action == 'add_user':
            self.permission_classes = []
        elif self.action == 'retrieve':
            self.permission_classes = [IsMember]
        return super().get_permissions()      
    
    def get_serializer_class(self):
        if self.action == 'add_user':
            return AddUserSerializer
        return super().get_serializer_class()
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            org = serializer.save()
            org.users.add(request.user)
            payload = {
                'status': 'success',
                'message': 'Organisation created successfully',
                'data': serializer.data
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

    @action(detail=True, methods=["post"], url_path="users")
    def add_user(self, request, *args, **kwargs):
        organisation = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, userId=serializer.validated_data['userId'])
        organisation.users.add(user)
        payload = {
            'status': 'success',
            'message': 'User added to organisation successfully'
        }
        return Response(payload, status=status.HTTP_200_OK)

