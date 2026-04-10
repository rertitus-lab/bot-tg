import os
import time
from flask import Flask, request
import telebot
from telebot import types

# =============== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) ===============
TOKEN = "8294974465:AAFfeR0krjHmDUwdQm7rO5N6VfnV8ZvFrOI"  # ⚠️ ЗАМЕНИ НА НОВЫЙ ТОКЕН!
SOFT_LINK = "https://www.mediafire.com/file/aulm7t7mu6388sc/Crack_Sbornik.exe/file"
IMAGE_URL = "https://i.ibb.co/KpKqsd8x/gg.png"

# ТВОЙ TELEGRAM ID (узнай у @userinfobot)
ADMIN_ID = 7859226148  # ⚠️ ПРОВЕРЬ, ЧТО ЭТО ТВОЙ ID!

# =============== ИНИЦИАЛИЗАЦИЯ ===============
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

# =============== КОМАНДА /REPORT (ИСПРАВЛЕНА) ===============
@bot.message_handler(commands=['report'])
def report_message(message):
    try:
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        user_username = f"@{message.from_user.username}" if message.from_user.username else "нет username"
        
        # Получаем текст жалобы (всё, что после /report)
        report_text = message.text.replace('/report', '').strip()
        
        if not report_text:
            bot.reply_to(message, "❌ Пожалуйста, напишите жалобу после команды.\n\nПример: `/report ссылка не работает`", parse_mode="Markdown")
            return
        
        # Проверяем, может ли бот писать админу (отправляем тестовое действие)
        try:
            bot.send_chat_action(ADMIN_ID, 'typing')
        except Exception as e:
            bot.reply_to(message, f"⚠️ Ошибка: администратор ещё не начал диалог с ботом.\n\nПожалуйста, сообщите администратору, чтобы он написал боту команду /start")
            print(f"Бот не может писать админу: {e}")
            return
        
        # Формируем сообщение для админа
        admin_message = f"📢 **НОВАЯ ЖАЛОБА!**\n\n"
        admin_message += f"👤 **От:** {user_name}\n"
        admin_message += f"🆔 **ID:** `{user_id}`\n"
        admin_message += f"📱 **Username:** {user_username}\n"
        admin_message += f"📝 **Текст жалобы:**\n{report_text}\n"
        admin_message += f"⏰ **Время:** {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Отправляем жалобу админу
        bot.send_message(ADMIN_ID, admin_message, parse_mode="Markdown")
        
        # Кнопка для быстрого ответа пользователю
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("💬 Ответить пользователю", callback_data=f"reply_{user_id}"))
        bot.send_message(ADMIN_ID, "🔧 Действия:", reply_markup=keyboard)
        
        # Подтверждение пользователю
        bot.reply_to(message, "✅ Ваша жалоба отправлена администратору! Мы рассмотрим её в ближайшее время.")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при отправке жалобы: {str(e)[:100]}")
        print(f"Ошибка в report_message: {e}")

# =============== ОТВЕТ ПОЛЬЗОВАТЕЛЮ ОТ АДМИНА ===============
@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def reply_to_user(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", show_alert=True)
        return
    
    user_id = int(call.data.split('_')[1])
    bot.answer_callback_query(call.id)
    
    msg = bot.send_message(call.message.chat.id, f"✏️ Введите ответ для пользователя с ID `{user_id}`:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, lambda m: send_reply_to_user(m, user_id))

def send_reply_to_user(message, user_id):
    reply_text = message.text.strip()
    try:
        bot.send_message(user_id, f"📢 **Ответ администратора:**\n\n{reply_text}", parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ Ответ отправлен пользователю {user_id}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Не удалось отправить ответ. Ошибка: {e}")

# =============== КОМАНДА /START ===============
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

# =============== АДМИН-ПАНЕЛЬ ===============
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

# =============== ОБЫЧНЫЕ КНОПКИ ===============
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
        bot.send_message(call.message.chat.id, f"🔗 **Ссылка:**\n{SOFT_LINK}", parse_mode="Markdown")
    
    elif call.data == "more":
        bot.answer_callback_query(call.id, "📸 Картинка отправлена!")
        bot.send_photo(call.message.chat.id, IMAGE_URL, caption="☢️ антивирус может ругаться на софт потому что это кряк ☢️")
    
    elif call.data == "share":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"👥 **Поделиться:**\n\nhttps://t.me/{bot.get_me().username}", parse_mode="Markdown")

# =============== АДМИН-ОБРАБОТЧИКИ ===============
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callback(call):
    global download_count, SOFT_LINK, IMAGE_URL
    
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", show_alert=True)
        return
    
    bot.answer_callback_query(call.id)
    
    if call.data == "admin_stats":
        bot.send_message(call.message.chat.id, f"📊 **Статистика:**\n\n📥 Скачиваний: {download_count}\n👥 Пользователей: {len(users)}", parse_mode="Markdown")
    
    elif call.data == "admin_users":
        bot.send_message(call.message.chat.id, f"👥 **Всего пользователей:** {len(users)}")
    
    elif call.data == "admin_change_link":
        msg = bot.send_message(call.message.chat.id, "📝 **Отправьте новую ссылку:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, change_link)
    
    elif call.data == "admin_change_image":
        msg = bot.send_message(call.message.chat.id, "🖼 **Отправьте новую ссылку на картинку:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, change_image)
    
    elif call.data == "admin_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 **Введите текст для рассылки:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, broadcast)

def change_link(message):
    global SOFT_LINK
    SOFT_LINK = message.text.strip()
    bot.send_message(message.chat.id, f"✅ Ссылка изменена!\n\n{SOFT_LINK}")

def change_image(message):
    global IMAGE_URL
    IMAGE_URL = message.text.strip()
    bot.send_message(message.chat.id, f"✅ Картинка изменена!\n\n{IMAGE_URL}")

def broadcast(message):
    text = message.text.strip()
    success = 0
    fail = 0
    
    bot.send_message(message.chat.id, "📢 **Начинаю рассылку...**", parse_mode="Markdown")
    
    for user_id in users:
        try:
            bot.send_message(user_id, f"📢 **Новость:**\n\n{text}", parse_mode="Markdown")
            success += 1
        except:
            fail += 1
        time.sleep(0.05)
    
    bot.send_message(message.chat.id, f"✅ **Рассылка завершена!**\n\n📨 Доставлено: {success}\n❌ Ошибок: {fail}")

# =============== WEBHOOK ДЛЯ RENDER ===============
@app.route(f'/{TOKEN}', methods=['POST'])
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

# =============== ЗАПУСК ===============
if __name__ == "__main__":
    # Удаляем старый webhook
    try:
        bot.remove_webhook()
        print("✅ Webhook удалён")
    except:
        pass
    time.sleep(1)
    
    # Устанавливаем новый webhook
    render_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'bot-tg-1-tw5w.onrender.com')
    webhook_url = f"https://{render_hostname}/{TOKEN}"
    
    try:
        bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook установлен: {webhook_url}")
    except Exception as e:
        print(f"❌ Ошибка установки webhook: {e}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
