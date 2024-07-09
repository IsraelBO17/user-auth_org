from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Organisation


User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        access_token = str(refresh.access_token)
        user = UserSerializer(instance=self.user)
        data = {
            'accessToken': access_token,
            'user': user.data,
            'user': {
                'userId': user.data['userId'],
                'firstName': user.data['firstName'],
                'lastName': user.data['lastName'],
                'email': user.data['email'],
                'phone': user.data['phone'],
            }
        }

        return data


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['firstName','lastName','email','password','phone','userId',]
        read_only_fields = ['userId']
    
    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            firstName=validated_data['firstName'],
            lastName=validated_data['lastName'],
            phone=validated_data['phone'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class AddUserSerializer(serializers.Serializer):
    userId = serializers.UUIDField()


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ['orgId','name','description']
        read_only_fields = ['orgId']


