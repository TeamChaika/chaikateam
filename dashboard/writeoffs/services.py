from contextlib import suppress
from datetime import datetime
from time import time

from django.contrib.auth.models import Permission
from django.db.models import Q
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.iiko import iiko_api
from core.telegram import telegram_bot
from authentication.models import User
from .models import Writeoff, WriteoffItem


def confirm_writeoff(writeoff: Writeoff, user: User):
    writeoff_items = WriteoffItem.objects.filter(
        writeoff_id=writeoff.id
    )
    response = load_writeoff(writeoff, writeoff_items)
    if response == 'SUCCESS':
        writeoff.processed_by = user
        writeoff.processed_at = time()
        writeoff.status = 'Sent'
        writeoff.save()


def deny_writeoff(writeoff: Writeoff, user: User):
    writeoff.processed_by = user
    writeoff.processed_at = time()
    writeoff.status = 'Denied'
    writeoff.save()


def load_writeoff(writeoff: Writeoff, writeoff_items: list[WriteoffItem]):
    document = {
        'documentNumber': 'DJ' + '0'*(
            6-len(str(writeoff.id))
        ) + str(writeoff.id),
        'dateIncoming': datetime.fromtimestamp(writeoff.created_at).isoformat(
            timespec='minutes'
        ),
        'status': 'NEW',
        'storeId': str(writeoff.store.id),
        'accountId': str(writeoff.reason.account_id),
        'comment': f'СПИСАНИЕ\n{writeoff.reason or ""}\n{writeoff.comment}',
        'items':
            [
                {'productId': item.product_id, 'amount': item.amount}
                for item in writeoff_items
            ]
    }
    response = iiko_api.load_writeoff(document)
    return response


def get_writeoff_message(
    writeoff: Writeoff,
    writeoff_items: list[WriteoffItem]
):
    nomenclature = iiko_api.get_nomenclature()['id']
    writeoff_items_string = ''
    comment = writeoff.comment if writeoff.comment else "Нет"
    document_number = 'DJ' + '0'*(6-len(str(writeoff.id))) + \
        str(writeoff.id)
    created_at = datetime.fromtimestamp(
        writeoff.created_at
    ).strftime('%d.%m.%Y %H:%M')
    for writeoff_item in writeoff_items:
        writeoff_items_string += '–' * 30 + \
            '\nНаименование: ' \
            f'{nomenclature.get(writeoff_item.product_id)}\n' \
            f'Количество: {writeoff_item.amount}\n'
    return f'<b>Новый запрос на создание списания:</b>\n\n' \
        f'<b>Номер:</b> {document_number}' \
        f'<b>Время:</b> {created_at}' \
        f'<b>Склад:</b> {writeoff.store.name}\n' \
        f'<b>Создал:</b> {writeoff.created_by.get_full_name()} ' \
        f'[{writeoff.created_by.username}]\n' \
        f'<b>Причина:</b> {writeoff.reason or "Нет"}\n' \
        f'<b>Комментарий:</b> {comment}\n' \
        f'<b>Количество позиций:</b> {len(writeoff_items)}\n\n' \
        f'<b>Товары:</b>\n{writeoff_items_string}'


def get_writeoff_keyboard(
    writeoff: Writeoff
):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            'Просмотр',
            url=f'https://chaika-iiko.ru/writeoffs/{writeoff.id}'
        )],
        [InlineKeyboardButton(
            'Подтвердить',
            callback_data=f'confirmWriteoff:{writeoff.id}'
        ), InlineKeyboardButton(
            'Отклонить',
            callback_data=f'denyWriteoff:{writeoff.id}'
        )]
    ])


def send_writeoff_confirmation(
    writeoff: Writeoff,
    writeoff_items: list[WriteoffItem]
):
    perm = Permission.objects.get(codename='is_disposer')
    for user in User.objects.filter(
        Q(telegram_id__isnull=False) &
        (
            Q(user_permissions=perm) |
            Q(groups__permissions=perm) |
            Q(is_superuser=True)
        ) & Q(stores=writeoff.store)
    ).distinct():
        with suppress(Exception):
            telegram_bot.send_message(
                chat_id=user.telegram_id,
                text=get_writeoff_message(writeoff, writeoff_items),
                parse_mode='HTML',
                reply_markup=get_writeoff_keyboard(writeoff),
                disable_web_page_preview=True
            )
