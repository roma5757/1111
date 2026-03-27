import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from database import init_db, add_participant, has_participated, get_next_code

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = os.getenv("ADMIN_ID")

# Инициализация бота и базы данных
init_db()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Глобальный флаг розыгрыша
raffle_active = False

# Команда для отправки сообщения с кнопкой
@dp.message(Command(commands=["send"]))
async def send_message(message: types.Message):
    global raffle_active
    if str(message.from_user.id) != ADMIN_ID:
        await message.reply("У вас нет доступа к этой команде.")
        return

    raffle_active = True  # включаем розыгрыш

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

# Команда для остановки розыгрыша
@dp.message(Command(commands=["stop"]))
async def stop_raffle(message: types.Message):
    global raffle_active
    if str(message.from_user.id) != ADMIN_ID:
        await message.reply("У вас нет доступа к этой команде.")
        return

    raffle_active = False
    await message.reply("Розыгрыш остановлен. Нажатия на старую кнопку больше не учитываются.")

# Обработка нажатия кнопки
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

        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Новый участник!\nUsername: @{user.username or 'нет'}\nID: {user.id}\nКод: {code}"
        )

        await callback.answer(f"Вы успешно участвовали! Ваш код: {code}", show_alert=True)

    except Exception as e:
        await callback.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)
        print(f"Error handling participation: {e}")

# Запуск бота
if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
