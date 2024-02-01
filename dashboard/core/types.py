from django.http import HttpRequest as DjangoHttpRequest
from django.contrib.auth.models import AnonymousUser

from authentication.models import User


class HttpRequest(DjangoHttpRequest):
    user: User | AnonymousUser
