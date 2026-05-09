import asyncio
import random
import re

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import TOKEN, ADMIN
from database import (
    has_premium,
    check_limit,
    add_request,
    remaining_requests,
    give_premium,
    get_premium_date,
)
from rarity import rarity

# ---------------- BOT ----------------

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# ---------------- KEYBOARDS ----------------

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ПОИСК"), KeyboardButton(text="ПРОФИЛЬ")],
        [KeyboardButton(text="ПОДПИСКА")]
    ],
    resize_keyboard=True
)

search_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="5 символов 🔒", callback_data="find_5")],
        [InlineKeyboardButton(text="6 символов 🆓", callback_data="find_6")]
    ]
)

def type_kb(length):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="С цифрами", callback_data=f"num_{length}")],
            [InlineKeyboardButton(text="Без цифр", callback_data=f"nonum_{length}")]
        ]
    )

def result_kb(length, nums):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Оставить", callback_data="keep"),
                InlineKeyboardButton(text="🔄 Скип", callback_data=f"skip_{length}_{int(nums)}")
            ]
        ]
    )

# ---------------- GENERATOR ----------------

def gen_username(length, nums=False):
    chars = "abcdefghijklmnopqrstuvwxyz"
    if nums:
        chars += "0123456789"
    return "".join(random.choice(chars) for _ in range(length))

def check_username(username):
    return random.choice([True, False])

# ---------------- START ----------------

@dp.message(CommandStart())
async def start(message: Message):
    user = message.from_user.username or "user"

    await message.answer(
        f"Привет, <b>{user}</b>.\n"
        "├ В данном боте можно найти\n"
        "├ Красивый свободный username",
        reply_markup=main_kb
    )

# ---------------- MENU ----------------

@dp.message(F.text == "ПОИСК")
async def search(message: Message):
    user = message.from_user.username or str(message.from_user.id)

    if user != ADMIN and not has_premium(user):
        if not check_limit(user):
            await message.answer("❌ Лимит 10 запросов / 48 часов исчерпан")
            return
        add_request(user)

    await message.answer("Выбери длину:", reply_markup=search_kb)

@dp.message(F.text == "ПРОФИЛЬ")
async def profile(message: Message):
    user = message.from_user.username or str(message.from_user.id)

    await message.answer(
        f"👤 Профиль\n\n"
        f"├ Подписка: {'Да' if has_premium(user) else 'Нет'}\n"
        f"├ До: {get_premium_date(user)}\n"
        f"└ Осталось запросов: {remaining_requests(user)}/10"
    )

@dp.message(F.text == "ПОДПИСКА")
async def sub(message: Message):
    await message.answer(
        f"⭐ Подписка 50 Stars / месяц\n"
        f"Писать: @{ADMIN}"
    )

# ---------------- SEARCH FLOW ----------------

@dp.callback_query(F.data.startswith("find_"))
async def find(call: CallbackQuery):
    length = int(call.data.split("_")[1])
    user = call.from_user.username or str(call.from_user.id)

    if length == 5 and user != ADMIN and not has_premium(user):
        await call.message.answer("🔒 5 символов только с подпиской")
        return

    await call.message.answer("Тип поиска:", reply_markup=type_kb(length))

@dp.callback_query(F.data.startswith("num_") | F.data.startswith("nonum_"))
async def generate(call: CallbackQuery):
    parts = call.data.split("_")
    nums = parts[0] == "num"
    length = int(parts[1])

    await send_result(call.message, length, nums)

async def send_result(message, length, nums):
    while True:
        username = gen_username(length, nums)

        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]{2,31}$", username):
            continue

        free = check_username(username)

        text = (
            "✅ <b>Найдено!</b>\n\n"
            f"├ Username: <code>{username}</code>\n"
            f"├ Редкость:\n{rarity(username)}\n"
            f"└ Статус: {'Свободен' if free else 'Занят'}"
        )

        await message.answer(text, reply_markup=result_kb(length, nums))
        break

# ---------------- SKIP / KEEP ----------------

@dp.callback_query(F.data == "keep")
async def keep(call: CallbackQuery):
    await call.message.answer("🎉 Поздравляем с обновкой!")

@dp.callback_query(F.data.startswith("skip_"))
async def skip(call: CallbackQuery):
    _, length, nums = call.data.split("_")
    await send_result(call.message, int(length), bool(int(nums)))

# ---------------- ADMIN ----------------

@dp.message(Command("premiumgive"))
async def premium(message: Message):
    if message.from_user.username != ADMIN:
        return

    _, user, days = message.text.split()
    give_premium(user.replace("@", ""), int(days))

    await message.answer("✅ Выдано")

# ---------------- RUN ----------------

async def main():
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
