import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from database import init_db, add_participant, has_participated, get_next_code, DB_NAME
import sqlite3

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID").strip())  # Важно: int

# Инициализация бота и базы данных
init_db()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

raffle_active = False  # Флаг текущего розыгрыша

# --- Команда для запуска розыгрыша ---
@dp.message(Command(commands=["send"]))
async def send_message(message: types.Message):
    global raffle_active
    if message.from_user.id != ADMIN_ID:
        await message.reply("У вас нет доступа к этой команде.")
        return

    raffle_active = True

    button = InlineKeyboardButton(text="Участвовать", callback_data="participate")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])

    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text="Нажмите кнопку, чтобы участвовать!",
            reply_markup=keyboard
        )
        await message.reply("Розыгрыш запущен. Сообщение отправлено.")
    except Exception as e:
        await message.reply(f"Ошибка отправки сообщения: {e}")

# --- Команда для остановки розыгрыша ---
@dp.message(Command(commands=["stop"]))
async def stop_raffle(message: types.Message):
    global raffle_active
    if message.from_user.id != ADMIN_ID:
        await message.reply("У вас нет доступа к этой команде.")
        return

    raffle_active = False
    await message.reply("Розыгрыш остановлен. Нажатия на старую кнопку больше не учитываются.")

# --- Обработка нажатия кнопки ---
@dp.callback_query(lambda c: c.data == "participate")
async def handle_participation(callback: types.CallbackQuery):
    global raffle_active
    user = callback.from_user

    if not raffle_active:
        await callback.answer("Розыгрыш сейчас не активен.", show_alert=True)
        return

    try:
        chat_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user.id)
        if chat_member.status in ["left", "kicked"]:
            await callback.answer("Подпишитесь на канал, чтобы участвовать.", show_alert=True)
            return

        if has_participated(user.id):
            await callback.answer("Вы уже участвовали.", show_alert=True)
            return

        code = get_next_code()
        add_participant(user.id, user.username or "", code)

        # Формируем отображение имени
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username_display = f"@{user.username}" if user.username else full_name if full_name else f"ID:{user.id}"

        # Уведомление админа
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Новый участник!\nUsername/Имя: {username_display}\nID: {user.id}\nКод: {code}"
        )

        await callback.answer(f"Вы успешно участвовали! Ваш код: {code}", show_alert=True)

    except Exception as e:
        await callback.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)
        print(f"Error handling participation: {e}")

# --- Команда /who для поиска участника по ID ---
@dp.message(Command(commands=["who"]))
async def who_is(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("У вас нет доступа к этой команде.")
        return

    args = message.get_args()
    if not args.isdigit():
        await message.reply("Используйте: /who <user_id>")
        return

    user_id = int(args)

    # --- Сначала ищем в базе ---
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, code FROM participants WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        username, code = row
        # Берём username из базы, имя/фамилию из базы не сохраняем, поэтому используем username
        username_display = f"@{username}" if username else f"ID:{user_id}"
        await message.reply(f"Найден в базе:\nUsername/Имя: {username_display}\nID: {user_id}\nКод: {code}")
        return

    # --- Если не найден в базе, пробуем через канал ---
    try:
        chat_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        user = chat_member.user
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username_display = f"@{user.username}" if user.username else full_name if full_name else f"ID:{user.id}"
        await message.reply(f"Пользователь в канале:\nUsername/Имя: {username_display}\nID: {user.id}")
        return
    except Exception:
        await message.reply(f"Пользователь с ID {user_id} не найден в базе и не состоит в канале.")

# --- Запуск бота ---
if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
