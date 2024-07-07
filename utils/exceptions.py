from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError


def custom_exception_handler(exc, context):
    response = exception_handler(exec, context)

    if response is not None:
        detail = response.data.get('detail')
        
        if isinstance(detail, list):
            try:
                detail = detail[0]
            except KeyError:
                detail = ''

        if detail:
            data = {'errors': detail}
        else:
            data = {'errors': 'Validation error!', 'data': response.data}
        data['status'] = exc.status_code
        return Response(data, status=response.status_code)

    return None

# def custom_exception_handler(exc, context):
#     # If it's a ValidationError, handle it specifically
#     if isinstance(exc, ValidationError):
#         # Get the detail dictionary from the exception
#         detail = exc.detail

#         # Return a 422 response with the validation errors
#         return Response(detail, status=422)

#     # Otherwise, let default exception handler handle it
#     return exception_handler(exc, context)


