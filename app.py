import os
import threading
from flask import Flask
import telebot
from telebot import types

TOKEN = "8773898221:AAGy67kpPvmxiHWCMagPdljvKWWX9fxz-FI"  # ЗАМЕНИТЕ НА СВОЙ ТОКЕН
SOFT_LINK = "https://www.mediafire.com/file/aulm7t7mu6388sc/zenin_crack.exe/file"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton("📥 Скачать софт", callback_data="download")
    button2 = types.InlineKeyboardButton("🎯 Подробнее", callback_data="more")
    keyboard.add(button1, button2)
    
    bot.send_message(message.chat.id, "ВЫБИРАЙТЕ СОФТ", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "download":
        bot.send_message(call.message.chat.id, f"🔗 Ссылка для скачивания:\n{SOFT_LINK}")
    
    elif call.data == "more":
        # Замени ссылку на свою картинку
        bot.send_photo(call.message.chat.id, "https://i.imgur.com/your_image.jpg", caption="📌 Подробнее о софте")

# ЭТО ВАЖНО: Flask сервер для Render
@app.route('/')
def index():
    return "Bot is running!"

@app.route('/healthz')
def health():
    return "OK"

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
