import os
import time
from flask import Flask, request
import telebot
from telebot import types

TOKEN = "8294974465:AAFfeR0krjHmDUwdQm7rO5N6VfnV8ZvFrOI"  # ⚠️ ЗАМЕНИТЕ НА НОВЫЙ ТОКЕН!
ADMIN_ID = 7859226148  # ⚠️ ЗАМЕНИТЕ НА СВОЙ ID

SOFT_LINK = "https://www.mediafire.com/file/aulm7t7mu6388sc/Crack_Sbornik.exe/file"
IMAGE_URL = "https://i.ibb.co/KpKqsd8x/gg.png"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Данные
users = set()
user_last_use = {}
blacklist = set()
waiting_for_report = {}
download_count = 0

# Трекер сообщений
message_tracker = {}  # {user_id: {"count": 0, "name": "", "username": ""}}
MESSAGES_FILE = "messages.txt"

# Файлы
BLACKLIST_FILE = "blacklist.txt"

# =============== ФУНКЦИИ ТРЕКЕРА ===============
def save_messages():
    with open(MESSAGES_FILE, 'w') as f:
        for uid, data in message_tracker.items():
            f.write(f"{uid}|{data['count']}|{data.get('name', '')}|{data.get('username', '')}\n")

def load_messages():
    global message_tracker
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split('|')
                    if len(parts) >= 2:
                        uid = int(parts[0])
                        count = int(parts[1])
                        name = parts[2] if len(parts) > 2 else ""
                        username = parts[3] if len(parts) > 3 else ""
                        message_tracker[uid] = {"count": count, "name": name, "username": username}
    print(f"✅ Загружен трекер: {len(message_tracker)} пользователей")

def add_message(uid, name, username):
    if uid in message_tracker:
        message_tracker[uid]["count"] += 1
    else:
        message_tracker[uid] = {"count": 1, "name": name, "username": username or ""}
    save_messages()

def get_messages(uid):
    return message_tracker.get(uid, {}).get("count", 0)

# =============== ФУНКЦИИ ЧС ===============
def save_blacklist():
    with open(BLACKLIST_FILE, 'w') as f:
        for uid in blacklist:
            f.write(f"{uid}\n")

def load_blacklist():
    global blacklist
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r') as f:
            blacklist = set(int(l.strip()) for l in f if l.strip())
    print(f"✅ Загружен ЧС: {len(blacklist)} пользователей")

def is_banned(uid):
    return uid in blacklist

def is_admin(uid):
    return uid == ADMIN_ID

def check_cd(uid):
    now = time.time()
    if uid in user_last_use:
        if now - user_last_use[uid] < 5:
            return int(5 - (now - user_last_use[uid]))
    return 0

def update_cd(uid):
    user_last_use[uid] = time.time()

# =============== ТРЕКЕР ВСЕХ СООБЩЕНИЙ ===============
@bot.message_handler(func=lambda message: True)
def track_all_messages(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    username = message.from_user.username or ""
    if not is_admin(uid):
        add_message(uid, name, username)

# =============== КОМАНДЫ ===============
@bot.message_handler(commands=['start'])
def start_command(message):
    uid = message.from_user.id
    if is_banned(uid):
        bot.send_message(uid, "❌ Вы забанены!")
        return
    
    users.add(uid)
    
    cd = check_cd(uid)
    if cd > 0:
        bot.send_message(uid, f"⏳ Подожди {cd} секунд!")
        return
    update_cd(uid)
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📥 Скачать софт", callback_data="download")
    btn2 = types.InlineKeyboardButton("🎯 Подробнее", callback_data="more")
    btn3 = types.InlineKeyboardButton("👥 Поделиться", callback_data="share")
    btn4 = types.InlineKeyboardButton("📢 Репорт", callback_data="report")
    kb.add(btn1, btn2, btn3, btn4)
    
    bot.send_message(uid, "Crack Sbornik - 💥 лучший сборник кряков именно для тебя!", reply_markup=kb)

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Нет доступа!")
        return
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("📝 Сменить ссылку", callback_data="admin_change_link"),
        types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("🖼 Сменить картинку", callback_data="admin_change_image"),
        types.InlineKeyboardButton("🚫 Забанить пользователя", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ Разбанить пользователя", callback_data="admin_unban"),
        types.InlineKeyboardButton("📋 Список забаненных", callback_data="admin_banlist"),
        types.InlineKeyboardButton("📊 Трекер сообщений", callback_data="admin_tracker")
    )
    bot.send_message(message.chat.id, "🔧 Админ-панель", reply_markup=kb)

@bot.message_handler(commands=['cancel'])
def cancel_command(message):
    uid = message.from_user.id
    if uid in waiting_for_report:
        del waiting_for_report[uid]
        bot.send_message(uid, "❌ Жалоба отменена")

# =============== КНОПКИ ПОЛЬЗОВАТЕЛЯ ===============
@bot.callback_query_handler(func=lambda call: call.data == "download")
def download_callback(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    
    cd = check_cd(uid)
    if cd > 0:
        bot.answer_callback_query(call.id, f"⏳ {cd} сек!", True)
        return
    update_cd(uid)
    
    global download_count
    download_count += 1
    bot.answer_callback_query(call.id, "✅ Ссылка отправлена!", False)
    bot.send_message(uid, f"🔗 Ссылка для скачивания:\n{SOFT_LINK}")

@bot.callback_query_handler(func=lambda call: call.data == "more")
def more_callback(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    
    cd = check_cd(uid)
    if cd > 0:
        bot.answer_callback_query(call.id, f"⏳ {cd} сек!", True)
        return
    update_cd(uid)
    
    bot.answer_callback_query(call.id, "📸", False)
    bot.send_photo(uid, IMAGE_URL, caption="☢️ антивирус может ругаться на софт потому что это кряк ☢️")

@bot.callback_query_handler(func=lambda call: call.data == "share")
def share_callback(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(uid, f"👥 Поделиться ботом:\n\nhttps://t.me/{bot.get_me().username}")

@bot.callback_query_handler(func=lambda call: call.data == "report")
def report_callback(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    
    cd = check_cd(uid)
    if cd > 0:
        bot.answer_callback_query(call.id, f"⏳ {cd} сек!", True)
        return
    update_cd(uid)
    
    bot.answer_callback_query(call.id)
    waiting_for_report[uid] = True
    bot.send_message(uid, "⚙️ Отправьте сообщение с жалобой.\n\n(Вы можете отменить командой /cancel)")

# =============== ОБРАБОТКА ЖАЛОБ ===============
@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_report)
def handle_report_text(m):
    uid = m.from_user.id
    text = m.text.strip()
    if uid in waiting_for_report:
        del waiting_for_report[uid]
    
    bot.send_message(uid, "✅ Ваша жалоба отправлена администратору!")
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💬 Ответить пользователю", callback_data=f"reply_{uid}"))
    bot.send_message(ADMIN_ID, f"📢 **НОВАЯ ЖАЛОБА!**\n\n👤 От: {m.from_user.first_name}\n🆔 ID: `{uid}`\n📱 Username: @{m.from_user.username if m.from_user.username else 'нет'}\n📝 Текст:\n{text}", parse_mode="Markdown", reply_markup=kb)

# =============== ОТВЕТ НА ЖАЛОБУ ===============
@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def reply_to_user(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    
    uid = int(call.data.split('_')[1])
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"✏️ Введите ответ для пользователя (ID: {uid}):")
    bot.register_next_step_handler(msg, lambda m: send_reply(m, uid))

def send_reply(message, uid):
    reply_text = message.text.strip()
    try:
        bot.send_message(uid, f"📢 **Ответ администратора:**\n\n{reply_text}", parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ Ответ отправлен пользователю {uid}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# =============== АДМИН-ФУНКЦИИ ===============
def change_link(m):
    global SOFT_LINK
    SOFT_LINK = m.text.strip()
    bot.send_message(m.chat.id, f"✅ Ссылка изменена!\n\n{SOFT_LINK}")

def change_image(m):
    global IMAGE_URL
    IMAGE_URL = m.text.strip()
    bot.send_message(m.chat.id, f"✅ Картинка изменена!\n\n{IMAGE_URL}")

def broadcast_msg(m):
    text = m.text.strip()
    success = 0
    fail = 0
    bot.send_message(m.chat.id, "📢 Начинаю рассылку...")
    for uid in users:
        if is_banned(uid):
            continue
        try:
            bot.send_message(uid, f"📢 **Новость от админа:**\n\n{text}", parse_mode="Markdown")
            success += 1
        except:
            fail += 1
        time.sleep(0.05)
    bot.send_message(m.chat.id, f"✅ Рассылка завершена!\n\n📨 Доставлено: {success}\n❌ Ошибок: {fail}")

def ban_user(m):
    try:
        uid = int(m.text.strip())
        if uid == ADMIN_ID:
            bot.send_message(m.chat.id, "❌ Нельзя забанить админа!")
            return
        blacklist.add(uid)
        save_blacklist()
        bot.send_message(m.chat.id, f"✅ Пользователь `{uid}` забанен!", parse_mode="Markdown")
        try:
            bot.send_message(uid, "❌ Вы были забанены в этом боте!")
        except:
            pass
    except:
        bot.send_message(m.chat.id, "❌ Ошибка! Введите ID.")

def unban_user(m):
    try:
        uid = int(m.text.strip())
        if uid in blacklist:
            blacklist.remove(uid)
            save_blacklist()
            bot.send_message(m.chat.id, f"✅ Пользователь `{uid}` разбанен!", parse_mode="Markdown")
            try:
                bot.send_message(uid, "✅ Вы были разбанены!")
            except:
                pass
        else:
            bot.send_message(m.chat.id, f"❌ Пользователь `{uid}` не в чёрном списке.", parse_mode="Markdown")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка! Введите ID.")

# =============== АДМИН-КНОПКИ ===============
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    
    if call.data == "admin_stats":
        bot.send_message(call.message.chat.id, f"📊 **Статистика:**\n\n📥 Скачиваний: {download_count}\n👥 Пользователей: {len(users)}", parse_mode="Markdown")
    
    elif call.data == "admin_users":
        bot.send_message(call.message.chat.id, f"👥 **Всего пользователей:** {len(users)}", parse_mode="Markdown")
    
    elif call.data == "admin_change_link":
        msg = bot.send_message(call.message.chat.id, "📝 Отправьте новую ссылку:")
        bot.register_next_step_handler(msg, change_link)
    
    elif call.data == "admin_change_image":
        msg = bot.send_message(call.message.chat.id, "🖼 Отправьте новую ссылку на картинку:")
        bot.register_next_step_handler(msg, change_image)
    
    elif call.data == "admin_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 Введите текст для рассылки:")
        bot.register_next_step_handler(msg, broadcast_msg)
    
    elif call.data == "admin_ban":
        msg = bot.send_message(call.message.chat.id, "🚫 Введите ID пользователя для бана:")
        bot.register_next_step_handler(msg, ban_user)
    
    elif call.data == "admin_unban":
        msg = bot.send_message(call.message.chat.id, "✅ Введите ID пользователя для разбана:")
        bot.register_next_step_handler(msg, unban_user)
    
    elif call.data == "admin_banlist":
        if blacklist:
            lst = "\n".join([str(uid) for uid in blacklist])
            bot.send_message(call.message.chat.id, f"📋 **Забаненные:**\n\n{lst}", parse_mode="Markdown")
        else:
            bot.send_message(call.message.chat.id, "📋 Чёрный список пуст.")
    
    elif call.data == "admin_tracker":
        if not message_tracker:
            bot.send_message(call.message.chat.id, "📊 Нет данных о сообщениях.")
            return
        sorted_users = sorted(message_tracker.items(), key=lambda x: x[1]["count"], reverse=True)[:20]
        text = "📊 **Топ пользователей по сообщениям:**\n\n"
        for i, (uid, data) in enumerate(sorted_users, 1):
            name = data.get('username') or data.get('name', str(uid))[:15]
            text += f"{i}. {name} — {data['count']} сообщений\n"
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

# =============== WEBHOOK ===============
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return 'OK', 200
    return 'Bad Request', 400

@app.route('/')
def index():
    return "Bot is running!"

if __name__ == "__main__":
    load_blacklist()
    load_messages()
    
    print(f"✅ Загружено: {len(blacklist)} в ЧС, {len(message_tracker)} в трекере")
    
    bot.remove_webhook()
    time.sleep(1)
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'bot-tg-1-x4tg.onrender.com')}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook установлен: {webhook_url}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
