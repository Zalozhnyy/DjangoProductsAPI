from django.core.exceptions import ValidationError
from django.http import JsonResponse
from rest_framework import exceptions, status


class Process500:
    def __init__(self, get_response):
        self._get_response = get_response

    def __call__(self, request):
        return self._get_response(request)

    def process_exception(self, request, exception: Exception):
        print(type(exception))
        if isinstance(exception, exceptions.ValidationError) or isinstance(exception, ValidationError):
            return JsonResponse({"code": status.HTTP_400_BAD_REQUEST, "message": "Validation Failed"},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse(
                {"code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                 "message": "INTERNAL_SERVER_ERROR",
                 'error': str(exception)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
