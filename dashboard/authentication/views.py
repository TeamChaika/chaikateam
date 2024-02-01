import re
import time

from typing import Any

from django.core.paginator import Paginator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.hashers import make_password

from core.types import HttpRequest
from core.decorators import hybrid_login, http_methods
from core.utils import get_pagination
from departments.models import Department
from .models import User, RegisterRequest
from .services import send_user_confirmation


class RegisterView(View):
    templates = {
        1: 'first-step.html',
        2: 'second-step.html',
        3: 'third-step.html'
    }
    handlers = {
        1: 'first_step',
        2: 'second_step',
        3: 'third_step'
    }
    extractions = {
        1: ['username', 'password', 'password_confirm'],
        2: ['department'],
        3: ['telegram_id']
    }

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect('/')
        self.context = {}
        form = request.session.get('register', {})
        self.form = form.copy()
        return super().dispatch(request, *args, **kwargs)

    def render(self, request: HttpRequest):
        if self.step == 2:
            self.context['departments'] = Department.objects.all()
        return render(
            request, f'register/{self.templates[self.step]}', self.context
        )

    def validate_base(self):
        if 'username' not in self.form or 'password' not in self.form:
            self.context['error_message'] = \
                'Пожалуйста, заполните все обязательные поля'
            return False
        if not re.match(r'^[\\+]?[0-9]{10,15}$', self.form['username']):
            self.context['error_message'] = \
                'Пожалуйста, введите номер корректно'
            return False
        if User.objects.filter(username=self.form['username']).exists() or \
                RegisterRequest.objects.filter(
                    username=self.form['username']
                ).exists():
            self.context['error_message'] = 'Данный номер уже используется'
            return False
        if not 8 <= len(self.form['password']) <= 64:
            self.context['error_message'] = \
                'Пароль должен содержать от 8 до 64 символов'
            return False
        return True

    def validate_first_step(self):
        if 'password_confirm' not in self.form:
            self.context['error_message'] = \
                'Пожалуйста, заполните все обязательные поля'
            return False
        if not 8 <= len(self.form['password_confirm']) <= 64:
            self.context['error_message'] = \
                'Пароль должен содержать от 8 до 64 символов'
            return False
        if self.form['password'] != self.form['password_confirm']:
            self.context['error_message'] = \
                'Пароли не совпадают, попробуйте ещё раз'
            return False
        return True

    def validate_second_step(self):
        department_id = self.form.get('department')
        if department_id and not Department.objects.filter(
            id=department_id
        ).exists():
            self.context['error_message'] = \
                'Выбран некорректный склад'
            return False
        return True

    def validate_third_step(self):
        telegram_id = self.form.get('telegram_id')
        telegram_id = int(telegram_id) \
            if telegram_id and telegram_id.isdigit() else None
        if telegram_id and \
           User.objects.filter(telegram_id=telegram_id).exists():
            self.context['error_message'] = \
                'Пользователь с таким Telegram уже существует'
            return False
        return True

    def validate_form(self):
        if not self.validate_base():
            self.step = 1
            return False
        if self.step == 1 and not self.validate_first_step():
            return False
        if self.step >= 2 and not self.validate_second_step():
            return False
        if self.step == 3 and not self.validate_third_step():
            return False
        return True

    def first_step(self, request: HttpRequest):
        request.session['register'] = {
            'username': self.form['username'],
            'password': self.form['password']
        }
        self.step = 2
        return self.render(request)

    def second_step(self, request: HttpRequest):
        request.session['department'] = self.form['department']
        self.step = 3
        return self.render(request)

    def third_step(self, request: HttpRequest):
        telegram_id = int(self.form['telegram_id']) \
            if self.form['telegram_id'] and \
            self.form['telegram_id'].isdigit() \
            else None
        department_id = int(self.form['department']) \
            if 'department' in self.form else None
        user = RegisterRequest(
            username=self.form['username'],
            password=make_password(self.form['password']),
            telegram_id=telegram_id,
            department_id=department_id
        )
        user.save()
        request.session.pop('register')
        send_user_confirmation(user)
        return render(request, 'register/finish.html')

    def get(self, request: HttpRequest):
        self.step = 1
        return self.render(request)

    def post(self, request: HttpRequest):
        self.step = int(request.POST.get('step'))
        for field in self.extractions[self.step]:
            self.form[field] = request.POST.get(field)
        valid = self.validate_form()
        if not valid:
            return self.render(request)
        return self.__getattribute__(self.handlers[self.step])(request)


@http_methods(['GET'])
@login_required(login_url='/login')
@permission_required('authentication.can_register_users')
def register_requests_view(request: HttpRequest):
    page = int(request.GET.get('page', '1'))
    requests = RegisterRequest.objects.select_related(
        'department'
    ).all().order_by('-id')
    paginator = Paginator(requests, 30)

    pagination = get_pagination(page, paginator.num_pages)

    return render(request, 'register/requests.html', context={
        'user': request.user,
        'requests': paginator.get_page(page),
        'pages': paginator.num_pages,
        'page': page,
        'pagination': pagination
    })


@http_methods(['POST'])
@csrf_exempt
@hybrid_login
@permission_required('authentication.can_create_users')
def confirm_request(request: HttpRequest, pk: int):
    user_request = get_object_or_404(RegisterRequest, id=pk)
    User(
        username=user_request.username, password=user_request.password,
        department_id=user_request.department_id,
        telegram_id=user_request.telegram_id
    ).save()
    user_request.delete()
    return HttpResponse(status=200)


@http_methods(['POST'])
@csrf_exempt
@hybrid_login
@permission_required('authentication.can_create_users')
def deny_request(request: HttpRequest, pk: int):
    user_request = get_object_or_404(RegisterRequest, id=pk)
    user_request.delete()
    return HttpResponse(status=200)


def login_view(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        if request.session.get('login_attempts'):
            if request.session.get('login_attempts') >= 5:
                if request.session.get('next_login') > time.time():
                    return render(
                        request, 'login.html',
                        context={
                            'error_message':
                            'Слишком много неудачных попыток входа.\n'
                            'Пожалуйста, попробуйте позже.'
                        }
                    )
                else:
                    request.session['login_attempts'] = 0
                    request.session.pop('next_login')

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if 'login_attempts' in request.session:
                request.session.pop('login_attempts')
            if 'next_login' in request.session:
                request.session.pop('next_login')
            return redirect('/')
        else:
            if not request.session.get('login_attempts'):
                request.session['login_attempts'] = 1
            else:
                request.session['login_attempts'] += 1
            if request.session.get('login_attempts') >= 5 and \
                    not request.session.get('next_login'):
                request.session['next_login'] = time.time() + 1800
            return render(
                request,
                'login.html',
                context={'error_message': 'Неверный логин или пароль'}
            )
    return render(request, 'login.html')


@login_required(login_url='/login')
def logout_view(request):
    logout(request)
    return redirect('/login')
