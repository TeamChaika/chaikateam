import hashlib
import hmac
import subprocess

from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from core.types import HttpRequest
from env import github_webhook_secret


@csrf_exempt
def github_webhook(request: HttpRequest):
    client_signature = request.META['HTTP_X_SIGNATURE']
    signature = hmac.new(
        github_webhook_secret,
        request.body,
        hashlib.sha1
    )
    expected_signature = 'sha1=' + signature.hexdigest()
    if not hmac.compare_digest(client_signature, expected_signature):
        return HttpResponseForbidden('Invalid signature header')

    subprocess.run(['./scripts/redeploy.sh'])

    return HttpResponse(status=200)
