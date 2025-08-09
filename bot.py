
import asyncio
import json
import os
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# --- Configuration du bot ---
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Le token du bot (variable d'environnement)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# --- Fichier pour stocker les données ---
data_file = "model_data.json"

def load_data():
    """Charge l'historique des prédictions depuis le fichier JSON."""
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            return json.load(f)
    return {"correct": [], "wrong": []}

def save_data(data):
    """Sauvegarde l'historique des prédictions dans le fichier JSON."""
    with open(data_file, "w") as f:
        json.dump(data, f)

# --- État temporaire des utilisateurs ---
user_state = {}

# --- Boutons de feedback ---
feedback_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("✅ Prédiction correcte", callback_data="correct"),
    InlineKeyboardButton("❌ Mauvaise prédiction", callback_data="wrong")
)

# --- Clavier principal ---
main_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("📊 Obtenir une prévision")
)

# --- Commande /start ---
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "👋 Bienvenue sur le bot de prédiction !\n"
        "Clique sur le bouton ci-dessous pour obtenir une estimation.",
        reply_markup=main_kb
    )

# --- Quand on demande une prévision ---
@dp.message_handler(lambda message: message.text == "📊 Obtenir une prévision")
async def forecast(message: types.Message):
    data = load_data()

    # Amélioration : pondérer plus les dernières bonnes prédictions
    if data["correct"]:
        poids_recent = sum(data["correct"][-5:]) / len(data["correct"][-5:])  # moyenne des 5 dernières
        poids_global = sum(data["correct"]) / len(data["correct"])
        base = (poids_recent * 0.7) + (poids_global * 0.3)
        offset = random.uniform(-0.15, 0.25)  # moins de variation aléatoire
        prediction = round(base + offset, 2)
    else:
        prediction = round(random.uniform(1.5, 3.0), 2)

    prix_vente = round(prediction - 0.2, 2)
    user_state[message.chat.id] = prediction

    await message.answer(
        f"📢 **Prédiction estimée :** `{prediction}`\n"
        f"💰 **Prix conseillé pour vendre :** `{prix_vente}`\n\n"
        "Merci de nous dire si cette prévision est correcte ⬇️",
        parse_mode="Markdown",
        reply_markup=feedback_markup
    )

# --- Quand l'utilisateur donne un feedback ---
@dp.callback_query_handler(lambda c: c.data in ["correct", "wrong"])
async def feedback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    prediction = user_state.get(user_id)

    if prediction:
        data = load_data()
        data[callback_query.data].append(prediction)
        save_data(data)

    if callback_query.data == "correct":
        await bot.send_message(user_id, "✅ Parfait ! Nous continuerons dans ce sens 💪")
    else:
        await bot.send_message(user_id, "⚠️ D'accord, nous allons améliorer nos prévisions 📈")

    await bot.answer_callback_query(callback_query.id)

# --- Lancement du bot ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
