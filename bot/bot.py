import asyncio

from aiogram import Bot, types, Dispatcher, F
from aiogram.filters import Command
from environs import Env
from services import process_register_request, process_waybill, \
    process_writeoff


env = Env()
env.read_env(override=True)

bot = Bot(env.str('BOT_TOKEN'))
dp = Dispatcher(bot)


@dp.message(Command('register'))
async def register(message: types.Message):
    return await message.answer(
        f'Ваш уникальный код для регистрации на сайте: '
        f'<b>{message.from_user.id}</b>\n'
        f'Вставьте его в запрашиваемое поле.', parse_mode='HTML'
    )


@dp.callback_query(
    F.data.startswith('confirmRegister:') or
    F.data.startswith('denyRegister:')
)
async def register_confirmation_handler(query: types.CallbackQuery):
    request_id = int(query.data.split(':')[1])
    return await process_register_request(
        query,
        'confirm' if query.data.startswith('confirm') else 'deny',
        request_id
    )


@dp.callback_query(
    F.data.startswith('confirmWaybill:') or
    F.data.startswith('denyWaybill:')
)
async def confirm_waybill(query: types.CallbackQuery):
    waybill_id = int(query.data.split(':')[1])
    return await process_waybill(
        query,
        'confirm' if query.data.startswith('confirm') else 'deny',
        waybill_id
    )


@dp.callback_query(
    F.data.startswith('confirmwriteoff:') or
    F.data.startswith('denywriteoff:')
)
async def confirm_writeoff(query: types.CallbackQuery):
    writeoff_id = int(query.data.split(':')[1])
    return await process_writeoff(
        query,
        'confirm' if query.data.startswith('confirm') else 'deny',
        writeoff_id
    )


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
