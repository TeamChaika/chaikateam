from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q, Subquery

from core.types import HttpRequest
from core.iiko import iiko_api
from core.iiko.decorators import hook_iiko_fail
from core.views import DocumentView
from core.decorators import http_methods, hybrid_login
from core.utils import get_pagination
from .models import Store, Waybill, WaybillItem
from .services import (
    confirm_waybill,
    deny_waybill,
    copy_waybill,
    cancel_waybill,
    send_waybill_confirmation
)


@method_decorator(
    [
        login_required(login_url="/login"),
        permission_required('authentication.can_add_waybills'),
        hook_iiko_fail
    ],
    name='dispatch')
class CreateWaybillView(DocumentView):
    model = Waybill
    item_model = WaybillItem
    rel = 'waybill'

    def before_dispatch(self, request: HttpRequest):
        self.context = {
            'user_stores': [store.name for store in request.user.stores.all()],
            'stores': [store.name for store in Store.objects.all()],
            'nomenclature': self.nomenclature['name'],
            'have_store': True
        }

    def render(self, request: HttpRequest):
        return render(request, 'waybills/create.html', context=self.context)

    def extract_stores(self, request: HttpRequest):
        user_store_name = request.POST.get('user_store_name')
        counteragent_store_name = request.POST.get('counteragent_store_name')
        try:
            user_store = Store.objects.get(name=user_store_name)
            counteragent_store = Store.objects.get(
                name=counteragent_store_name
            )
        except Store.DoesNotExist:
            self.context['error_message'] = \
                'Пожалуйста, используйте предлагаемые наименования!'
            return self.render(request)
        if user_store.id == counteragent_store.id:
            self.context['error_message'] = \
                'Пожалуйста, не используйте один и тот же склад!'
            return self.render(request)
        return user_store, counteragent_store

    def post(self, request: HttpRequest):
        extracted = self.extract_stores(request)
        if isinstance(extracted, HttpResponse):
            return extracted
        user_store, counteragent_store = extracted
        created = self.create_document(
            request,
            store=user_store,
            counteragent=counteragent_store,
            comment=request.POST.get('comment'),
            created_by=request.user
        )
        if isinstance(created, HttpResponse):
            return created
        waybill, waybill_items = created
        send_waybill_confirmation(waybill, waybill_items)
        self.context['success_message'] = \
            'Накладная успешно создана и отправлена на подтверждение!'
        return self.render(request)


@method_decorator(
    [
        login_required(login_url="/login"),
        permission_required('authentication.can_add_waybills'),
        hook_iiko_fail
    ],
    name='dispatch')
class EditWaybillView(DocumentView):
    def before_dispatch(self, request: HttpRequest):
        self.items: dict[str, WaybillItem] = {
            item.product_id: item
            for item in WaybillItem.objects.filter(
                waybill_id=self.waybill.id
            )
        }
        self.updated = False
        self.context = {
            'waybill_id': self.waybill.id,
            'have_store': True,
            'nomenclature': self.nomenclature['name'],
        }

    def dispatch(self, request: HttpRequest, pk: int, *args, **kwargs):
        self.fetch_waybill(request, pk)
        return super().dispatch(request, pk, *args, **kwargs)

    def render(self, request: HttpRequest):
        self.context['items'] = (
            (self.nomenclature['id'].get(str(pk)), item.amount)
            for pk, item in self.items.items()
        ) if isinstance(self.items, dict) else (
            (self.nomenclature['id'].get(str(item.product_id)), item.amount)
            for item in self.items
        )
        return render(request, 'waybills/edit.html', context=self.context)

    def fetch_waybill(self, request: HttpRequest, pk: int):
        self.waybill = get_object_or_404(
            Waybill, id=pk, status='Created'
        )
        if self.waybill.store not in request.user.stores.all():
            raise PermissionDenied()

    def update_items(self, request: HttpRequest, items: list[tuple]):
        create = []
        update = []
        for name, amount in items:
            if not name or len(name) == 0 or not amount or float(amount) == 0:
                self.context['error_message'] = \
                    'Пожалуйста, заполните поля корректно!'
                return self.render(request)
            if name not in self.nomenclature['name']:
                self.context['error_message'] = \
                    'Пожалуйста, используйте предлагаемые наименования!'
                return self.render(request)
            if name in self.items:
                if self.items[name].amount != float(amount):
                    self.items[name].amount = float(amount)
                    update.append(self.items[name])
            else:
                create.append(
                    WaybillItem(
                        waybill_id=self.waybill.id,
                        product_id=self.nomenclature['name'].get(name),
                        amount=float(amount)
                    )
                )
        if create:
            WaybillItem.objects.bulk_create(create)
            if not self.updated:
                self.updated = True
        if update:
            WaybillItem.objects.bulk_update(update, ['amount'])
            if not self.updated:
                self.updated = True

    def delete_items(self, request: HttpRequest):
        names = set(request.POST.getlist('products_names[]', []))
        for name, item in self.items.items():
            if name not in names:
                item.delete()
                if not self.updated:
                    self.updated = True

    def post(self, request: HttpRequest, pk: int):
        collected = self.collect_items(request)
        if isinstance(collected, HttpResponse):
            return collected
        collected = tuple(collected)
        self.update_items(request, collected)
        self.delete_items(request)
        if not self.updated:
            self.context['error_message'] = 'Данные не были изменены'
            return self.render(request)
        self.items = WaybillItem.objects.filter(
            waybill_id=self.waybill.id
        )
        send_waybill_confirmation(self.waybill, self.items, 'updated')
        self.context['success_message'] = 'Данные успешно изменены!'
        return self.render(request)


@http_methods(['GET'])
@login_required(login_url='/login')
@permission_required('authentication.can_view_waybills')
def waybill_view(request: HttpRequest, pk: int):
    user_stores = set(
        request.user.stores.all().values_list('id', flat=True)
    )
    if not user_stores:
        raise PermissionDenied()
    waybill = get_object_or_404(
        Waybill.objects.select_related('store', 'counteragent', 'created_by'),
        id=pk
    )
    if not user_stores.intersection(
        [waybill.store.id, waybill.counteragent.id]
    ):
        raise PermissionDenied()
    nomenclature = iiko_api.get_nomenclature()['id']
    return render(
        request,
        'waybills/item.html',
        context={
            'waybill': waybill,
            'created_at': datetime.fromtimestamp(waybill.created_at),
            'processed_at': datetime.fromtimestamp(waybill.processed_at)
            if waybill.processed_at else None,
            'items': (
                (nomenclature.get(str(item.product_id)), item.amount)
                for item in WaybillItem.objects.filter(waybill=waybill)
            ),
            'stores': user_stores
        }
    )


def waybills_view(waybill_type: str):
    @http_methods(['GET'])
    @login_required(login_url="/login")
    @permission_required('authentication.can_view_waybills')
    def inner(request: HttpRequest):
        user_stores = request.user.stores.all().values_list('id', flat=True)
        if not user_stores:
            return render(
                request, 'waybills/index.html',
                context={'have_store': False}
            )
        nomenclature = iiko_api.get_nomenclature()['name']
        page = int(request.GET.get('page', '1'))
        search = request.GET.get('search')
        search_product = nomenclature.get(search)
        query = Q()
        if search_product:
            query &= Q(id__in=Subquery(
                WaybillItem.objects.filter(
                    product_id=search_product
                ).distinct(
                    'waybill_id'
                ).values_list('waybill_id', flat=True)
            ))
        if waybill_type == 'incoming':
            query &= Q(counteragent__in=user_stores)
        elif waybill_type == 'outgoing':
            query &= Q(store__in=user_stores)
        else:
            query &= (
                Q(store__in=user_stores) |
                Q(counteragent__in=user_stores)
            )
        waybills = Waybill.objects.filter(query).select_related(
            'store', 'counteragent'
        ).order_by('-id')

        paginator = Paginator(waybills, 30)
        pagination = get_pagination(page, paginator.num_pages)

        return render(
            request,
            'waybills/index.html',
            context={
                'stores': set(user_stores),
                'type': waybill_type,
                'have_store': True,
                'search': search if search_product else None,
                'waybills': [
                    (
                        waybill,
                        datetime.fromtimestamp(waybill.created_at)
                    )
                    for waybill in paginator.get_page(page)
                ],
                'nomenclature': nomenclature,
                'pages': paginator.num_pages,
                'page': page,
                'pagination': pagination
            }
        )
    return inner


@http_methods(['POST'])
@csrf_exempt
@hybrid_login
@permission_required('authentication.can_add_waybills')
@hook_iiko_fail
def process_waybill(request: HttpRequest, pk: int, action: str):
    waybill = get_object_or_404(
        Waybill.objects.select_related('store', 'counteragent', 'created_by'),
        id=pk
    )
    if waybill.status != 'Created' and action != 'copy':
        return HttpResponse('Bad Request: Already processed', status=400)
    user_stores = set(
        request.user.stores.all().values_list('id', flat=True)
    )
    if not user_stores.intersection(
        [waybill.store.id, waybill.counteragent.id]
    ):
        return HttpResponse(status=403)
    if action == 'copy':
        if not request.user.has_perm('authentication.is_accountant'):
            return HttpResponse(status=403)
        copy_waybill(waybill, request.user)
        return HttpResponse(status=200)
    if waybill.store.id in user_stores:
        if action == 'cancel':
            cancel_waybill(waybill, request.user)
            return HttpResponse(status=200)
    if waybill.counteragent.id in user_stores:
        if action == 'confirm':
            confirm_waybill(waybill, request.user)
            return HttpResponse(status=200)
        elif action == 'deny':
            deny_waybill(waybill, request.user)
            return HttpResponse(status=200)
    return HttpResponse('Bad Request', status=400)
