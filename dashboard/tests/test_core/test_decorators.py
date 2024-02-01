from django.test import TestCase, RequestFactory
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from authentication.models import User
from core.decorators import http_methods, hybrid_login


class TestDecorators(TestCase):

    def setUp(self):
        (self.user, _) = User.objects.get_or_create(
            username='test', password='test', telegram_id=10000
        )
        self.factory = RequestFactory()

    def test_http_methods_pass(self):
        @http_methods(['GET'])
        def view(_):
            return HttpResponse()
        request = self.factory.get('/')
        request.user = self.user
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_http_methods_fails(self):
        @http_methods(['GET'])
        def view(_):
            return HttpResponse()
        request = self.factory.post('/')
        request.user = self.user
        response = view(request)
        self.assertEqual(response.status_code, 405)

    def test_hybrid_login_local_pass(self):
        @csrf_exempt
        @hybrid_login
        def view(_):
            return HttpResponse()
        request = self.factory.get('/')
        request.META['Telegram-User'] = '10000'
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_hybrid_login_local_fails(self):
        @csrf_exempt
        @hybrid_login
        def view(_):
            return HttpResponse()
        request = self.factory.get('/')
        request.META['Telegram-User'] = '10001'
        with self.assertRaises(Http404):
            response = view(request)

        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '198.65.24.132'
        request.META['Telegram-User'] = '10000'
        response = view(request)
        self.assertEqual(response.status_code, 401)

    def test_hybrid_login_remote_pass(self):
        @csrf_exempt
        @hybrid_login
        def view(_):
            return HttpResponse()
        request = self.factory.post('/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '198.65.24.132'
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_hybrid_login_remote_fails(self):
        @csrf_exempt
        @hybrid_login
        def view(_):
            return HttpResponse()
        request = self.factory.post('/')
        request.META['REMOTE_ADDR'] = '198.65.24.132'
        response = view(request)
        self.assertEqual(response.status_code, 401)
