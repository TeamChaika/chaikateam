from typing import Any
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View

from core.types import HttpRequest
from spending.models import Spending, Category, Agreed


@method_decorator([login_required(login_url="/login")], name='dispatch')
class SpendingView(View):
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        self.context = {
            'have_department': bool(request.user.department),
            'categories': list(Category.objects.all()),
            'agreed': list(Agreed.objects.all()),
        }
        return super().dispatch(request, *args, **kwargs)

    def render(self, request: HttpRequest):
        return render(request, 'spending/index.html', self.context)

    def post(self, request: HttpRequest):
        name = request.POST.get('name')
        amount = request.POST.get('amount')
        category_id = request.POST.get('category')
        agreed_id = request.POST.get('agreed')
        if not all([name, amount, category_id, agreed_id]):
            self.context['error_message'] = \
                'Пожалуйста, введите данные корректно!'
            return self.render(request)
        if not amount.isdigit():
            self.context['error_message'] = \
                'Пожалуйста, введите данные корректно!'
            return self.render(request)
        category = get_object_or_404(Category, id=int(category_id))
        agreed = get_object_or_404(Agreed, id=int(agreed_id))
        spending = Spending(
            department=request.user.department,
            category=category,
            user=request.user,
            name=name,
            amount=int(amount),
            agreed=agreed
        )
        spending.save()
        self.context['success_message'] = \
            'Новая запись расходов успешно добавлена!'
        return self.render(request)

    def get(self, request: HttpRequest):
        return self.render(request)
