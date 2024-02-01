import requests

from aiogram.types import CallbackQuery


def send_request(url: str, user_id: int):
    headers = {
        'Telegram-User': user_id
    }
    return requests.post(url, headers=headers)


async def process_register_request(
    query: CallbackQuery, action: str, request_id: int
):
    response = send_request(
        f'https://iiko.chaika.team/register-requests/{request_id}/{action}',
        query.from_user.id
    )
    if response.status_code == 200:
        await query.message.delete()
        if action == 'confirm':
            return await query.answer(
                'Пользователь успешно зарегистрирован!', show_alert=True
            )
        else:
            return await query.answer(
                'Заявка на регистрацию успешно отклонена!', show_alert=True
            )
    elif response.status_code == 404:
        await query.message.delete()
        return await query.answer(
            'Заявка отсутствует. Она была обработана или удалена.',
            show_alert=True
        )
    else:
        return await query.answer(
            'Что-то пошло не так, попробуйте позже!', show_alert=True
        )


async def process_waybill(
    query: CallbackQuery, action: str, waybill_id: int
):
    response = send_request(
        f'https://iiko.chaika.team/waybills/{waybill_id}/{action}',
        query.from_user.id
    )
    if response.status_code == 200:
        await query.message.delete()
        if action == 'confirm':
            return await query.answer(
                'Накладная успешно создана!', show_alert=True
            )
        else:
            return await query.answer(
                'Накладная успешно отклонена!', show_alert=True
            )
    elif response.status_code == 400 and 'Already processed' in response.text:
        await query.message.delete()
        return await query.answer(
            'Данная накладная уже обработана!', show_alert=True
        )
    else:
        return await query.answer(
            'Что-то пошло не так, попробуйте позже!', show_alert=True
        )


async def process_writeoff(
    query: CallbackQuery, action: str, writeoff_id: int
):
    response = send_request(
        f'https://iiko.chaika.team/writeoffs/{writeoff_id}/{action}',
        query.from_user.id
    )
    if response.status_code == 200:
        await query.message.delete()
        if action == 'confirm':
            return await query.answer(
                'Списание успешно создано!', show_alert=True
            )
        else:
            return await query.answer(
                'Списание успешно отклонено!', show_alert=True
            )
    elif response.status_code == 400 and 'Already processed' in response.text:
        await query.message.delete()
        return await query.answer(
            'Данное списание уже обработано!', show_alert=True
        )
    else:
        return await query.answer(
            'Что-то пошло не так, попробуйте позже!', show_alert=True
        )
