from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Organisation
from rest_framework import status
from rest_framework.exceptions import APIException

User = get_user_model()

class CustomValidationError(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    def __init__(self, detail=None, code=None):
        super().__init__(detail, code=code)

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id','email','password','first_name','last_name','phone']
    
    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    
    # def validate(self, data):
    #     if data:
    #         # print(data)
    #         raise CustomValidationError()
    #     return data
    


