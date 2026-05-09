import asyncio
import random
import re
from datetime import timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties

from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from config import TOKEN, ADMIN
from database import (
    has_premium,
    get_premium_date,
    give_premium,
    check_limit,
    add_request,
    remaining_requests
)

from rarity import rarity

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()

# ---------------- КНОПКИ ----------------

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="ПОИСК"),
            KeyboardButton(text="ПРОФИЛЬ")
        ],
        [
            KeyboardButton(text="ПОДПИСКА")
        ]
    ],
    resize_keyboard=True
)

search_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="5 символов 🔒",
                callback_data="find_5"
            )
        ],
        [
            InlineKeyboardButton(
                text="6 символов 🆓",
                callback_data="find_6"
            )
        ]
    ]
)

def chars_kb(length):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="С цифрами",
                    callback_data=f"num_{length}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Без цифр",
                    callback_data=f"nonum_{length}"
                )
            ]
        ]
    )

def result_kb(length, numbers):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Оставить",
                    callback_data="keep"
                ),

                InlineKeyboardButton(
                    text="🔄 Скип",
                    callback_data=f"skip_{length}_{int(numbers)}"
                )
            ]
        ]
    )

# ---------------- ЛОГИКА ----------------

def generate_username(length, numbers=False):
    letters = "abcdefghijklmnopqrstuvwxyz"

    if numbers:
        letters += "0123456789"

    return "".join(
        random.choice(letters)
        for _ in range(length)
    )

def check_username(username):
    # фейковая проверка
    return random.choice([True, False])

async def send_result(message, length, numbers):
    while True:
        username = generate_username(length, numbers)

        valid = re.match(
            r"^[a-zA-Z][a-zA-Z0-9_]{4,31}$",
            username
        )

        if not valid:
            continue

        free = check_username(username)

        text = (
            "✅ <b>Найдено!</b>\n\n"
            f"├ Username: <code>{username}</code>\n"
            f"├ Редкость:\n{rarity(username)}\n"
            f"└ Статус: "
            f"{'Свободен ✅' if free else 'Занят ❌'}\n\n"
            "          @StarsSearchBot"
        )

        await message.answer(
            text,
            reply_markup=result_kb(
                length,
                numbers
            )
        )

        break

# ---------------- START ----------------

@dp.message(CommandStart())
async def start(message: Message):
    username = message.from_user.username or "user"

    text = (
        f"Привет, <b>{username}</b>.\n"
        "├ В данном боте можно найти\n"
        "├ Красивый свободный username"
    )

    await message.answer(
        text,
        reply_markup=main_kb
    )

# ---------------- ПОИСК ----------------

@dp.message(F.text == "ПОИСК")
async def search(message: Message):
    username = (
        message.from_user.username
        or str(message.from_user.id)
    )

    if (
        username != ADMIN
        and not has_premium(username)
    ):

        left = remaining_requests(username)

        if left <= 0:
            await message.answer(
                "❌ Лимит исчерпан.\n"
                "├ 10 запросов / 48 часов\n"
                f"└ Для безлимита: @{ADMIN}"
            )
            return

        await message.answer(
            f"🆓 Осталось запросов: {left}/10"
        )

    await message.answer(
        "Выбери длину username:",
        reply_markup=search_kb
    )

@dp.callback_query(F.data.startswith("find_"))
async def choose_type(call: CallbackQuery):
    length = call.data.split("_")[1]

    username = (
        call.from_user.username
        or str(call.from_user.id)
    )

    if (
        length == "5"
        and username != ADMIN
        and not has_premium(username)
    ):

        await call.message.answer(
            "🔒 5 символов только по подписке.\n"
            f"Покупка: @{ADMIN}"
        )

        return

    await call.message.answer(
        "Выбери тип поиска:",
        reply_markup=chars_kb(length)
    )

@dp.callback_query(
    F.data.startswith("num_")
)

@dp.callback_query(
    F.data.startswith("nonum_")
)

async def find_username(call: CallbackQuery):
    data = call.data.split("_")

    numbers = data[0] == "num"
    length = int(data[1])

    username = (
        call.from_user.username
        or str(call.from_user.id)
    )

    if (
        username != ADMIN
        and not has_premium(username)
    ):

        if not check_limit(username):
            await call.message.answer(
                "❌ Лимит запросов исчерпан.\n"
                "├ 10 запросов / 48 часов\n"
                f"└ Для безлимита: @{ADMIN}"
            )

            return

        add_request(username)

    await call.message.answer(
        "🔍 Поиск username..."
    )

    await send_result(
        call.message,
        length,
        numbers
    )

# ---------------- СКИП ----------------

@dp.callback_query(
    F.data.startswith("skip_")
)

async def skip_username(call: CallbackQuery):
    data = call.data.split("_")

    length = int(data[1])
    numbers = bool(int(data[2]))

    await send_result(
        call.message,
        length,
        numbers
    )

@dp.callback_query(F.data == "keep")
async def keep_username(call: CallbackQuery):
    await call.message.answer(
        "🎉 Поздравляем с обновкой!"
    )

# ---------------- ПРОФИЛЬ ----------------

@dp.message(F.text == "ПРОФИЛЬ")
async def profile(message: Message):
    username = (
        message.from_user.username
        or str(message.from_user.id)
    )

    premium = (
        "Есть ✅"
        if has_premium(username)
        else "Нет ❌"
    )

    left = remaining_requests(username)

    text = (
        "👤 <b>Профиль</b>\n\n"
        f"├ Подписка: {premium}\n"
        f"├ Действует до: "
        f"{get_premium_date(username)}\n"
        f"└ Осталось запросов: "
        f"{left}/10"
    )

    await message.answer(text)

# ---------------- ПОДПИСКА ----------------

@dp.message(F.text == "ПОДПИСКА")
async def sub(message: Message):
    text = (
        "⭐ Подписка стоит 50 Stars / месяц.\n\n"
        f"Для покупки отправь Stars @{ADMIN}"
    )

    await message.answer(text)

# ---------------- АДМИН ----------------

@dp.message(Command("premiumgive"))
async def premium_give(message: Message):

    if (
        message.from_user.username
        != ADMIN
    ):
        return

    args = message.text.split()

    if len(args) != 3:
        await message.answer(
            "/premiumgive username days"
        )

        return

    username = args[1].replace("@", "")
    days = int(args[2])

    give_premium(username, days)

    await message.answer(
        f"✅ @{username} получил "
        f"Premium на {days} дней"
    )

# ---------------- ЗАПУСК ----------------

async def main():
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
