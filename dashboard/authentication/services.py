from contextlib import suppress

from django.contrib.auth.models import Permission
from django.db.models import Q
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.telegram import telegram_bot
from .models import User, RegisterRequest


def get_user_message(request: RegisterRequest):
    return f'<b>Новый запрос на регистрацию:</b>\n\n' \
        f'<b>Номер телефона:</b> {request.username}\n' \
        f'<b>Заведение:</b> {request.department or "Не выбрано"}'


def get_user_keyboard(request: RegisterRequest):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            'Подтвердить', callback_data=f'confirmRegister:{request.id}'
        ), InlineKeyboardButton(
            'Отклонить', callback_data=f'denyRegister:{request.id}'
        )]
    ])


def send_user_confirmation(request: RegisterRequest):
    perm = Permission.objects.get(codename='can_register_users')
    for user in User.objects.filter(
        Q(telegram_id__isnull=False) & (
            Q(user_permissions=perm) |
            Q(groups__permissions=perm) |
            Q(is_superuser=True)
        )
    ).distinct():
        with suppress(Exception):
            telegram_bot.send_message(
                chat_id=user.telegram_id,
                text=get_user_message(request),
                parse_mode='HTML',
                reply_markup=get_user_keyboard(request),
                disable_web_page_preview=True
            )
