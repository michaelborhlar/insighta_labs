from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_map = {
            400: 'Bad request',
            404: 'Profile not found',
            422: 'Invalid parameter type',
            500: 'Internal server error',
        }
        detail = response.data.get('detail', '') if isinstance(response.data, dict) else str(response.data)
        message = str(detail) if detail else error_map.get(response.status_code, 'An error occurred')
        response.data = {
            'status': 'error',
            'message': message,
        }

    return response
