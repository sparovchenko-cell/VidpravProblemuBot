import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart
from aiogram import F
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Стан машини
class ReportProblem(StatesGroup):
    waiting_for_topic = State()
    waiting_for_media = State()
    waiting_for_description = State()

# Теми проблем
topic_dict = {
    "1. Дороги і ями": "1. Дороги і ями",
    "2. Сміття і бур’яни": "2. Сміття і бур’яни",
    "3. Дитячі майданчики": "3. Дитячі майданчики",
    "4. Парки і сквери": "4. Парки і сквери",
    "5. Тротуари і переходи": "5. Тротуари і переходи",
    "6. Недобудови і руїни": "6. Недобудови і руїни",
    "7. Школи і дитсадки": "7. Школи і дитсадки",
    "8. Вода і каналізація": "8. Вода і каналізація",
    "9. Комунальні будівлі": "9. Комунальні будівлі",
    "10. Архітектура і фасади": "10. Архітектура і фасади",
    "11. Освітлення": "11. Освітлення",
    "12. Міська рада": "12. Міська рада",
    "13. Катерина Бабіч": "13. Катерина Бабіч",
    "14. Пропозиції / Ідеї": "14. Пропозиції / Ідеї",
    "15. Інше": "15. Інше",
}

# Клавіатура тем
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=key)] for key in topic_dict.keys()
    ],
    resize_keyboard=True
)

# /start
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("👋 Привіт! Оберіть тему проблеми:", reply_markup=keyboard)
    await state.set_state(ReportProblem.waiting_for_topic)

# Обробка теми
@dp.message(F.text.in_(topic_dict.keys()), ReportProblem.waiting_for_topic)
async def topic_chosen(message: Message, state: FSMContext):
    topic = topic_dict[message.text]
    await state.update_data(topic=topic)
    await state.set_state(ReportProblem.waiting_for_media)
    await message.answer("📸 Надішліть фото або відео проблеми:")

# Прийом медіа
@dp.message((F.photo | F.video | F.document), ReportProblem.waiting_for_media)
async def media_received(message: Message, state: FSMContext):
    file_id = None
    file_type = None

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"

    await state.update_data(file_id=file_id, file_type=file_type)
    await state.set_state(ReportProblem.waiting_for_description)
    await message.answer("✏️ Введіть короткий опис проблеми:")

# Прийом опису
@dp.message(ReportProblem.waiting_for_description)
async def description_received(message: Message, state: FSMContext):
    user_data = await state.get_data()
    file_id = user_data["file_id"]
    file_type = user_data["file_type"]
    topic = user_data["topic"]
    description = message.text
    user_id = message.from_user.id

    caption = f"<b>Надійшло нове звернення:</b>\n<b>Тема:</b> {topic}\n<b>Опис:</b> {description}\n<b>Користувач:</b> <code>{user_id}</code>"

    if file_type == "photo":
        await bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=caption)
    elif file_type == "video":
        await bot.send_video(chat_id=ADMIN_ID, video=file_id, caption=caption)
    elif file_type == "document":
        await bot.send_document(chat_id=ADMIN_ID, document=file_id, caption=caption)

    await message.answer("✅ Дякуємо! Ваше звернення передано.", reply_markup=keyboard)
    await state.clear()

# Запуск
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dp.run_polling(bot)
