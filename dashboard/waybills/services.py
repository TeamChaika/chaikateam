from contextlib import suppress
from datetime import datetime
from time import time

from django.contrib.auth.models import Permission
from django.db.models import Q
from dicttoxml import dicttoxml
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from authentication.models import User
from core.iiko import iiko_api
from core.telegram import telegram_bot
from .models import Waybill, WaybillItem


def confirm_waybill(waybill: Waybill, user: User):
    waybill_items = WaybillItem.objects.filter(waybill_id=waybill.id)
    waybill.processed_by = user
    response = load_waybill(waybill, waybill_items)
    if response.get('valid'):
        waybill.status = 'Sent'
        waybill.processed_at = time()
        waybill.save()


def deny_waybill(waybill: Waybill, user: User):
    waybill.status = 'Denied'
    waybill.processed_by = user
    waybill.processed_at = time()
    waybill.save()


def copy_waybill(waybill: Waybill, user: User):
    duplicate = Waybill(
        store=waybill.store,
        counteragent=waybill.counteragent,
        comment=waybill.comment,
        status='Created',
        created_by=user
    )
    duplicate.save()
    waybill_items = WaybillItem.objects.filter(waybill_id=waybill.id)
    items = []
    for item in waybill_items:
        items.append(WaybillItem(
            waybill=duplicate, product_id=item.product_id,
            amount=item.amount
        ))
    WaybillItem.objects.bulk_create(items)
    send_waybill_confirmation(duplicate, items)


def cancel_waybill(waybill: Waybill, user: User):
    waybill.status = 'Cancelled'
    waybill.processed_by = user
    waybill.processed_at = time()
    waybill.save()


def load_waybill(waybill: Waybill, waybill_items: list[WaybillItem]):
    comment = f'Отправил: {waybill.created_by.get_full_name()} ' \
        f'[{waybill.created_by.username}] ' \
        f'со склада {waybill.store.name}\n'
    comment += f'Принял: {waybill.processed_by.get_full_name()} ' \
        f'[{waybill.processed_by.username}] ' \
        f'на склад {waybill.counteragent.name}'
    document = {
        'documentNumber': 'DJ' + '0'*(6-len(str(waybill.id))) +
        str(waybill.id),
        'dateIncoming': datetime.fromtimestamp(
            waybill.created_at
        ).isoformat(timespec='seconds'),
        'useDefaultDocumentTime': True,
        'defaultStoreId': str(waybill.store.id),
        'comment': comment,
        'items':
            [
                {
                    'productId': str(item.product_id),
                    'price': 0.0,
                    'amount': item.amount
                } for item in waybill_items
            ]
    }
    document = dicttoxml(document, custom_root='document', attr_type=False)
    response = iiko_api.load_waybill(document)
    return response


def get_waybill_message(
    waybill: Waybill,
    waybill_items: list[WaybillItem],
    event: str
):
    nomenclature = iiko_api.get_nomenclature()['id']
    waybill_items_string = ''
    for waybill_item in waybill_items:
        waybill_items_string += '–' * 30 + \
            '\nНаименование: ' \
            f'{nomenclature.get(str(waybill_item.product_id))}\n' \
            f'Количество: {waybill_item.amount}\n'

    document_number = 'DJ' + '0'*(6-len(str(waybill.id))) + \
        str(waybill.id)
    created_at = datetime.fromtimestamp(
        waybill.created_at
    ).strftime('%d.%m.%Y %H:%M')
    title = 'Новый запрос на создание накладной:' \
        if event == 'created' else 'Запрос на создание накладной обновлён:'

    return f'<b>{title}</b>\n\n' \
        f'<b>Номер:</b> {document_number}' \
        f'<b>Время:</b> {created_at}' \
        f'<b>Откуда:</b> {waybill.store.name}\n' \
        f'<b>Куда:</b> {waybill.counteragent.name}\n' \
        f'<b>Создал:</b> {waybill.created_by.get_full_name()} ' \
        f'[{waybill.created_by.username}]\n' \
        f'<b>Комментарий:</b> ' \
        f'{waybill.comment if waybill.comment else "Нет"}\n' \
        f'<b>Количество позиций:</b> {len(waybill_items)}\n\n' \
        f'<b>Товары:</b>\n{waybill_items_string}'


def get_waybill_buttons(waybill_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            'Просмотр',
            url=f'https://iiko.chaika.team/waybills/{waybill_id}')
         ],
        [InlineKeyboardButton(
            'Подтвердить',
            callback_data=f'confirmWaybill:{waybill_id}'
        ), InlineKeyboardButton(
            'Отклонить',
            callback_data=f'denyWaybill:{waybill_id}')
        ]]
    )


def send_waybill_confirmation(
    waybill: Waybill,
    waybill_items: list[WaybillItem],
    event: str = 'created'
):
    perm = Permission.objects.get(codename='can_add_waybills')
    for user in User.objects.filter(
        Q(telegram_id__isnull=False) &
        (
            Q(user_permissions=perm) |
            Q(groups__permissions=perm) |
            Q(is_superuser=True)
        ) &
        Q(stores=waybill.counteragent)
    ).distinct():
        with suppress(Exception):
            telegram_bot.send_message(
                chat_id=user.telegram_id,
                text=get_waybill_message(waybill, waybill_items, event),
                parse_mode='HTML',
                reply_markup=get_waybill_buttons(waybill.id),
                disable_web_page_preview=True
            )
