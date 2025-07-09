import asyncio
import logging
import types

from aiogram import Bot, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm import state
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram3.db import create_table, insert_user, show_users

TOKEN = "1631569628:AAGIReQ7XYB69DJzEbJUHwfSc9Q-SWo5Qj4"
dp = Dispatcher()

class Form(StatesGroup):
    name = State()
    email = State()

builder = InlineKeyboardBuilder()
builder.add(
    InlineKeyboardButton(
        text="Malumotlarni ko'rish",
        callback_data="show_data"
    )
)

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(f"Assalomu alaykum {message.from_user.first_name}"
                         f"\n\nRo'yxatdan o'tish uchun /form bosing.")

@dp.message(Command("form"))
async def registration(message: Message, state: FSMContext):
    await message.answer("Ismingizni kiriting:")
    await state.set_state(Form.name)

@dp.message(Form.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"Emailingizni kiriting")
    await state.set_state(Form.email)

@dp.message(Form.email)
async def get_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)

    data = await state.get_data()
    name = data.get("name")
    email = data.get("email")
    print(name, email)
    insert_user(name, email)

    await message.answer("Malumotlaringiz saqlandi", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "show_data")
async def show_data(call: CallbackQuery):
    all_users = show_users()
    if not all_users:
        await call.message.answer("Hech qanday userlar yo'q")
        return

    text = ""
    for user in all_users:
        user_id, name, email = user
        text += f"\nID: {user_id}\nName: {name}\nEmail: {email}"

    await call.message.answer(text)

async def main():
    create_table()
    bot = Bot(TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

