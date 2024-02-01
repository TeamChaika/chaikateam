from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q

from core.views import DocumentView
from core.decorators import http_methods, hybrid_login
from core.iiko import iiko_api
from core.iiko.decorators import hook_iiko_fail
from core.types import HttpRequest
from core.utils import get_pagination
from .models import Store, Writeoff, WriteoffItem, WriteoffReason
from .services import (
    confirm_writeoff,
    deny_writeoff,
    send_writeoff_confirmation
)


@method_decorator(
    [
        login_required(login_url="/login"),
        permission_required('authentication.can_add_writeoffs'),
        hook_iiko_fail
    ],
    name='dispatch')
class CreateWriteoffView(DocumentView):
    model = Writeoff
    item_model = WriteoffItem
    rel = 'writeoff'

    def before_dispatch(self, request: HttpRequest):
        self.context = {
            'user_stores': [store.name for store in request.user.stores.all()],
            'reasons': WriteoffReason.objects.all(),
            'nomenclature': self.nomenclature['name'],
            'have_store': True
        }

    def render(self, request: HttpRequest):
        return render(request, 'writeoffs/create.html', context=self.context)

    def extract_store(self, request: HttpRequest):
        user_store_name = request.POST.get('user_store_name')
        try:
            user_store = Store.objects.get(name=user_store_name)
        except Store.DoesNotExist:
            self.context['error_message'] = \
                'Пожалуйста, используйте предлагаемые наименования!'
            return self.render(request)
        return user_store

    def extract_reason(self, request: HttpRequest):
        reason_id = request.POST.get('reason')
        if not reason_id:
            self.context['error_message'] = \
                'Пожалуйста, заполните поля корректно!'
            return self.render(request)
        try:
            reason = WriteoffReason.objects.get(id=reason_id)
        except WriteoffReason.DoesNotExist:
            self.context['error_message'] = \
                'Пожалуйста, используйте предлагаемые наименования!'
            return self.render(request)
        return reason

    def post(self, request: HttpRequest):
        extracted = self.extract_store(request)
        if isinstance(extracted, HttpResponse):
            return extracted
        store = extracted
        extracted = self.extract_reason(request)
        if isinstance(extracted, HttpResponse):
            return extracted
        reason = extracted
        created = self.create_document(
            request,
            store=store,
            reason=reason,
            comment=request.POST.get('comment'),
            created_by=request.user
        )
        if isinstance(created, HttpResponse):
            return created
        writeoff, writeoff_items = created
        send_writeoff_confirmation(writeoff, writeoff_items)
        self.context['success_message'] = \
            'Списание успешно создано и отправлено на подтверждение!'
        return self.render(request)


@http_methods(['GET'])
@login_required(login_url='/login')
@permission_required('authentication.can_view_writeoffs')
def writeoff_view(request: HttpRequest, pk: int):
    user_stores = set(
        request.user.stores.all().values_list('id', flat=True)
    )
    if not user_stores:
        raise PermissionDenied()
    writeoff = get_object_or_404(
        Writeoff.objects.select_related('store', 'created_by'),
        id=pk
    )
    if writeoff.store.id not in user_stores:
        raise PermissionDenied()
    nomenclature = iiko_api.get_nomenclature()['id']
    return render(
        request,
        'writeoffs/item.html',
        context={
            'writeoff': writeoff,
            'created_at': datetime.fromtimestamp(writeoff.created_at),
            'processed_at': datetime.fromtimestamp(writeoff.processed_at)
            if writeoff.processed_at else None,
            'items': (
                (nomenclature.get(str(item.product_id)), item.amount)
                for item in WriteoffItem.objects.filter(writeoff=writeoff)
            )
        }
    )


@http_methods(['GET'])
@login_required(login_url="/login")
@permission_required('authentication.can_view_writeoffs')
def writeoffs_view(request: HttpRequest):
    if not request.user.stores.all():
        return render(
            request,
            'writeoffs/index.html',
            context={'have_store': False}
        )
    page = int(request.GET.get('page', '1'))
    writeoffs = Writeoff.objects.filter(
        Q(store__in=request.user.stores.all())
    ).order_by('-id')

    paginator = Paginator(writeoffs, 30)
    pagination = get_pagination(page, paginator.num_pages)

    return render(
        request,
        'writeoffs/index.html',
        context={
            'have_store': bool(request.user.stores.all()),
            'writeoffs': [
                (
                    writeoff,
                    datetime.fromtimestamp(
                        writeoff.created_at
                    )
                )
                for writeoff in paginator.get_page(page)
            ],
            'pages': paginator.num_pages,
            'page': page,
            'pagination': pagination
        }
    )


@http_methods(['POST'])
@csrf_exempt
@hybrid_login
@permission_required('authentication.is_disposer')
@hook_iiko_fail
def process_writeoff(request: HttpRequest, pk: int, action: str):
    writeoff = get_object_or_404(
        Writeoff.objects.select_related('store', 'created_by'),
        id=pk
    )
    if writeoff.status != 'Created':
        return HttpResponse('Bad Request: Already processed', status=400)
    if writeoff.store not in request.user.stores.all():
        return HttpResponse(status=403)
    if action == 'confirm':
        confirm_writeoff(writeoff, request.user)
        return HttpResponse(status=200)
    elif action == 'deny':
        deny_writeoff(writeoff, request.user)
        return HttpResponse(status=200)
    return HttpResponse('Bad Request', status=400)
