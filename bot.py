import os
import random
import string
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession
from database import init_db, add_participant, has_participated

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # id канала для проверки подписки (например: -1001234567890)
ADMIN_ID = os.getenv("ADMIN_ID")      # id админа для уведомлений

# Инициализация бота и базы данных
init_db()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def generate_code(length: int = 8) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Команда для отправки сообщения с кнопкой в канал
@dp.message(Command(commands=["send"]))
async def send_message(message: types.Message):
    try:
        if str(message.from_user.id) != ADMIN_ID:
            await message.reply("У вас нет доступа к этой команде.")
            return

        # Создаем inline кнопку
        button = InlineKeyboardButton(text="Участвовать", callback_data="participate")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])

        await bot.send_message(
            chat_id=CHANNEL_ID,
            text="Нажмите кнопку, чтобы участвовать!",
            reply_markup=keyboard
        )
        await message.reply("Сообщение отправлено.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")

# Обработка нажатия inline-кнопки
@dp.callback_query(lambda c: c.data == "participate")
async def handle_participation(callback: types.CallbackQuery):
    user = callback.from_user
    try:
        # Проверка подписки
        chat_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user.id)
        if chat_member.status in ["left", "kicked"]:
            await callback.answer("Подпишитесь на канал, чтобы участвовать.", show_alert=True)
            return

        # Проверка, участвовал ли пользователь
        if has_participated(user.id):
            await callback.answer("Вы уже участвовали.", show_alert=True)
            return

        # Генерация уникального кода
        code = generate_code()
        add_participant(user.id, user.username or "", code)

        # Уведомление админа
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Новый участник!\nUsername: @{user.username}\nID: {user.id}\nКод: {code}"
        )

        await callback.answer("Вы успешно участвовали! Ваш код отправлен администратору.", show_alert=True)

    except Exception as e:
        await callback.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)
        print(f"Error handling participation: {e}")

# Запуск бота (поллинг)
if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))