
import asyncio
import json
import os
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Простая база: храним успешные предсказания
data_file = "model_data.json"

def load_data():
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            return json.load(f)
    return {"correct": [], "wrong": []}

def save_data(data):
    with open(data_file, "w") as f:
        json.dump(data, f)

user_state = {}
feedback_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("Был прав", callback_data="correct"),
    InlineKeyboardButton("Не угадал", callback_data="wrong")
)

main_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Дай прогноз"))

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("Добро пожаловать! Нажми кнопку ниже для прогноза.", reply_markup=main_kb)

@dp.message_handler(lambda message: message.text == "Дай прогноз")
async def forecast(message: types.Message):
    data = load_data()
    if data["correct"]:
        base = sum(data["correct"]) / len(data["correct"])
        offset = random.uniform(-0.2, 0.3)
        prediction = round(base + offset, 2)
    else:
        prediction = round(random.uniform(1.5, 3.0), 2)

    sell = round(prediction - 0.2, 2)
    user_state[message.chat.id] = prediction
    await message.answer(f"Предположительный коэффициент: {prediction}
Рекомендуем продавать около: {sell}", reply_markup=feedback_markup)

@dp.callback_query_handler(lambda c: c.data in ["correct", "wrong"])
async def feedback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    prediction = user_state.get(user_id)
    if prediction:
        data = load_data()
        data[callback_query.data].append(prediction)
        save_data(data)

    if callback_query.data == "correct":
        await bot.send_message(user_id, "Отлично, будем стараться дальше!")
    else:
        await bot.send_message(user_id, "Простите, будем улучшаться!")

    await bot.answer_callback_query(callback_query.id)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
