from functools import wraps
from traceback import print_exc

from django.http import HttpResponse
from requests.exceptions import Timeout, ConnectTimeout

from core.types import HttpRequest
from .exceptions import RequestFailed


def hook_iiko_fail(function):
    @wraps(function)
    def wrap(request: HttpRequest, *args, **kwargs):
        try:
            return function(request, *args, **kwargs)
        except (RequestFailed, Timeout, ConnectTimeout):
            print_exc()
            return HttpResponse('Cannot connect to Iiko', status=424)
    return wrap
