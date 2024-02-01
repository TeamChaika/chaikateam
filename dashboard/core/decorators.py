from functools import wraps
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_protect

from .types import HttpRequest
from authentication.models import User


def http_methods(methods: list[str]):
    def decorator(view):
        @wraps(view)
        def wrap(request: HttpRequest, *args, **kwargs):
            if request.method not in methods:
                return HttpResponse('Method Not Allowed', status=405)
            return view(request, *args, **kwargs)
        return wrap
    return decorator


def hybrid_login(view):
    @wraps(view)
    def wrap(request: HttpRequest, *args, **kwargs):
        if request.META.get('REMOTE_ADDR') == '127.0.0.1' \
             and 'Telegram-User' in request.META:
            request.user = get_object_or_404(
                User, telegram_id=request.META.get('Telegram-User')
            )
            return view(request, *args, **kwargs)
        elif not hasattr(request, 'user') or not request.user.is_authenticated:
            return HttpResponse('Unauthorized', status=401)
        return csrf_protect(view)(request, *args, **kwargs)
    return wrap
