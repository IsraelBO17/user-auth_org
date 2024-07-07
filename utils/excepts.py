from typing import Any, Union
from django.core.exceptions import ValidationError as DjangoCoreValidationError
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response


from rest_framework.views import exception_handler


class CustomException(Exception):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        status: str = None,
        message: Union[int, str] = None,
        errors: Any = None,
    ):
        self.status_code = status_code
        self.message = message
        self.errors = errors
        self.status = status


class QuerySetException(Exception):
    def __init__(self, errors: list, message: str):
        self.errors = errors
        self.message = message


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            "status": response.status_code,
            "message": response.data,
        }

    if isinstance(exc, CustomException):
        response = Response(
            {"statusCode": exc.status_code, "message": exc.message, "status": ""},
            status=exc.status_code,
        )
        
    elif isinstance(exc, QuerySetException):
        response = Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": exc.message,
                "errors": exc.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    elif isinstance(exc, DjangoCoreValidationError):
        response = Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": exc.message,
                "errors": exc.error_list,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
        
    elif isinstance(exc, AuthenticationFailed):
        response = Response(
            {
                "statusCode": status.HTTP_401_UNAUTHORIZED,
                "message": "Authentication failed",
                "status": "Bad request",
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    return response