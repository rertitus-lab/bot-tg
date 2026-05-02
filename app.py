import os
import time
import random
import string
from flask import Flask, request
import telebot
from telebot import types

# =============== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) ===============
TOKEN = "8294974465:AAFfeR0krjHmDUwdQm7rO5N6VfnV8ZvFrOI"  # ⚠️ ЗАМЕНИ НА НОВЫЙ ТОКЕН!
ADMIN_ID = 7859226148  # ⚠️ ЗАМЕНИ НА СВОЙ ID

SOFT_LINK = "https://www.mediafire.com/file/giyvpt6yuy9so7m/Crack_Sbornik.exe/file"
IMAGE_URL = "https://i.ibb.co/YBXZt30f/ggdoksraz.png"
CRACK_PLUS_LINK = "https://www.mediafire.com/file/2w6a3y18ke8vr94/Crack_Plus.exe/file"
CRACK_PLUS_PRICE = 2500

# =============== ИНИЦИАЛИЗАЦИЯ ===============
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

download_count = 0
users = set()
user_last_use = {}
waiting_for_report = {}
blacklist = set()
message_tracker = {}
coins_data = {}

BLACKLIST_FILE = "blacklist.txt"
MESSAGE_FILE = "messages.txt"
COINS_FILE = "coins.txt"

# =============== ФУНКЦИЯ ГЕНЕРАЦИИ КЛЮЧА ===============
def generate_key():
    parts = []
    for _ in range(4):
        part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        parts.append(part)
    return '-'.join(parts)

# =============== ФУНКЦИИ ЗАГРУЗКИ/СОХРАНЕНИЯ ===============
def load_blacklist():
    global blacklist
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r') as f:
            blacklist = set(int(line.strip()) for line in f if line.strip())
    print(f"✅ Загружен ЧС: {len(blacklist)} пользователей")

def save_blacklist():
    with open(BLACKLIST_FILE, 'w') as f:
        for uid in blacklist:
            f.write(f"{uid}\n")

def load_messages():
    global message_tracker
    if os.path.exists(MESSAGE_FILE):
        with open(MESSAGE_FILE, 'r') as f:
            for line in f:
                if '|' in line:
                    uid, count, username, name = line.strip().split('|')
                    message_tracker[int(uid)] = {"count": int(count), "username": username, "name": name}
    print(f"✅ Загружен трекер: {len(message_tracker)} пользователей")

def save_messages():
    with open(MESSAGE_FILE, 'w') as f:
        for uid, data in message_tracker.items():
            f.write(f"{uid}|{data['count']}|{data['username']}|{data['name']}\n")

def update_message_count(uid, username, name):
    if uid in message_tracker:
        message_tracker[uid]["count"] += 1
    else:
        message_tracker[uid] = {"count": 1, "username": username or "", "name": name}
    save_messages()

def load_coins():
    global coins_data
    if os.path.exists(COINS_FILE):
        with open(COINS_FILE, 'r') as f:
            for line in f:
                if '|' in line:
                    uid, val = line.strip().split('|')
                    coins_data[int(uid)] = int(val)
    print(f"✅ Загружены монеты: {len(coins_data)} пользователей")

def save_coins():
    with open(COINS_FILE, 'w') as f:
        for uid, val in coins_data.items():
            f.write(f"{uid}|{val}\n")

# =============== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===============
def is_banned(uid): return uid in blacklist
def is_admin(uid): return uid == ADMIN_ID
def get_coins(uid): return coins_data.get(uid, 0)
def add_coins(uid, amt): 
    coins_data[uid] = get_coins(uid) + amt
    save_coins()
def remove_coins(uid, amt):
    if get_coins(uid) >= amt:
        coins_data[uid] -= amt
        save_coins()
        return True
    return False

def check_cd(uid):
    now = time.time()
    if uid in user_last_use and now - user_last_use[uid] < 5:
        return int(5 - (now - user_last_use[uid]))
    return 0

def update_cd(uid):
    user_last_use[uid] = time.time()

def track_user(message):
    uid = message.from_user.id
    if not is_admin(uid):
        update_message_count(uid, message.from_user.username or "", message.from_user.first_name)

# =============== ДИАГНОСТИКА ===============
@bot.message_handler(commands=['test'])
def test_command(m):
    track_user(m)
    bot.send_message(m.chat.id, "✅ Бот работает! Команды: /start, /buy, /admin")

# =============== КОМАНДЫ ===============
@bot.message_handler(commands=['start'])
def start(m):
    track_user(m)
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
    track_user(m)
    uid = m.from_user.id
    if is_banned(uid):
        bot.send_message(uid, "❌ Вы забанены!")
        return
    coins = get_coins(uid)
    if coins >= CRACK_PLUS_PRICE:
        remove_coins(uid, CRACK_PLUS_PRICE)
        key = generate_key()
        bot.send_message(uid, f"🎉 CRACK PLUS КУПЛЕН!\n\n🔗 Ссылка:\n{CRACK_PLUS_LINK}\n\n🔑 Ключ активации: {key}\n\n💰 Остаток монет: {get_coins(uid)}")
    else:
        bot.send_message(uid, f"❌ Не хватает монет! У вас {coins}, надо {CRACK_PLUS_PRICE}")

@bot.message_handler(commands=['admin'])
def admin(m):
    track_user(m)
    if not is_admin(m.from_user.id):
        bot.send_message(m.chat.id, "❌ Нет доступа!")
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("📝 Сменить ссылку", callback_data="admin_change_link"),
        types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("🖼 Сменить картинку", callback_data="admin_change_image"),
        types.InlineKeyboardButton("🚫 Забанить", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ Разбанить", callback_data="admin_unban"),
        types.InlineKeyboardButton("📋 Список ЧС", callback_data="admin_banlist"),
        types.InlineKeyboardButton("📊 Трекер", callback_data="admin_tracker"),
        types.InlineKeyboardButton("💰 Выдать монеты", callback_data="admin_give_coins")
    )
    bot.send_message(m.chat.id, "🔧 Админ-панель", reply_markup=kb)

@bot.message_handler(commands=['cancel'])
def cancel(m):
    track_user(m)
    uid = m.from_user.id
    if uid in waiting_for_report:
        del waiting_for_report[uid]
        bot.reply_to(m, "❌ Отменено")

# =============== КНОПКИ ПОЛЬЗОВАТЕЛЯ ===============
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    
    # Обработка ответа на жалобу
    if call.data.startswith('reply_'):
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
            return
        user_id = int(call.data.split('_')[1])
        bot.answer_callback_query(call.id, "✏️ Введите текст ответа", show_alert=False)
        msg = bot.send_message(call.message.chat.id, f"✏️ Введите ответ для пользователя (ID: {user_id}):")
        bot.register_next_step_handler(msg, lambda m: send_reply(m, user_id))
        return
    
    # КД для остальных кнопок
    cd = check_cd(uid)
    if cd > 0 and call.data not in ["balance", "crack_plus"]:
        bot.answer_callback_query(call.id, f"⏳ {cd} сек!", True)
        return
    update_cd(uid)
    
    # Обработка кнопок
    if call.data == "download":
        global download_count
        download_count += 1
        bot.answer_callback_query(call.id, "✅ Ссылка отправлена!")
        bot.send_message(uid, f"🔗 {SOFT_LINK}")
    
    elif call.data == "more":
        bot.answer_callback_query(call.id, "📸")
        bot.send_photo(uid, IMAGE_URL, caption="☢️ антивирус может ругаться на софт")
    
    elif call.data == "share":
        bot.answer_callback_query(call.id)
        bot.send_message(uid, f"👥 Поделиться:\nhttps://t.me/{bot.get_me().username}")
    
    elif call.data == "balance":
        bot.answer_callback_query(call.id)
        bot.send_message(uid, f"💰 Баланс: {get_coins(uid)} монет")
    
    elif call.data == "crack_plus":
        bot.answer_callback_query(call.id)
        bot.send_message(uid, "🌐 **Crack Plus**\n\nНапишите /buy чтобы купить!\n/start дает +10 монет!\nCrack Plus дает лучшую оптимизацию и больше функций!", parse_mode="Markdown")
    
    elif call.data == "report":
        waiting_for_report[uid] = True
        bot.answer_callback_query(call.id)
        bot.send_message(uid, "✍️ Напишите текст жалобы (/cancel для отмены)")
    
    # Админ-кнопки
    elif is_admin(uid) and call.data.startswith('admin_'):
        if call.data == "admin_stats":
            bot.answer_callback_query(call.id)
            bot.send_message(uid, f"📊 Статистика:\n📥 Скачиваний: {download_count}\n👥 Пользователей: {len(users)}")
        
        elif call.data == "admin_users":
            bot.answer_callback_query(call.id)
            bot.send_message(uid, f"👥 Всего пользователей: {len(users)}")
        
        elif call.data == "admin_change_link":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(uid, "📝 Отправьте новую ссылку:")
            bot.register_next_step_handler(msg, change_link)
        
        elif call.data == "admin_change_image":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(uid, "🖼 Отправьте новую ссылку на картинку:")
            bot.register_next_step_handler(msg, change_image)
        
        elif call.data == "admin_broadcast":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(uid, "📢 Введите текст для рассылки:")
            bot.register_next_step_handler(msg, broadcast)
        
        elif call.data == "admin_ban":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(uid, "🚫 Введите ID:")
            bot.register_next_step_handler(msg, ban_user)
        
        elif call.data == "admin_unban":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(uid, "✅ Введите ID:")
            bot.register_next_step_handler(msg, unban_user)
        
        elif call.data == "admin_banlist":
            bot.answer_callback_query(call.id)
            if blacklist:
                bot.send_message(uid, f"📋 Забаненные:\n" + "\n".join(str(x) for x in blacklist))
            else:
                bot.send_message(uid, "📋 ЧС пуст")
        
        elif call.data == "admin_tracker":
            bot.answer_callback_query(call.id)
            if not message_tracker:
                bot.send_message(uid, "📊 Нет данных о сообщениях.")
                return
            top = sorted(message_tracker.items(), key=lambda x: x[1]["count"], reverse=True)[:20]
            text = "📊 **Топ пользователей по сообщениям:**\n\n"
            for i, (uidd, d) in enumerate(top, 1):
                name = d.get('username') or d.get('name', str(uidd))[:15]
                text += f"{i}. {name} — {d['count']} сообщений\n"
            bot.send_message(uid, text, parse_mode="Markdown")
        
        elif call.data == "admin_give_coins":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(uid, "💰 Введите: ID количество")
            bot.register_next_step_handler(msg, give_coins)

def send_reply(message, user_id):
    reply_text = message.text.strip()
    if not reply_text:
        bot.send_message(message.chat.id, "❌ Ответ не может быть пустым!")
        return
    try:
        bot.send_message(user_id, f"📢 **Ответ администратора:**\n\n{reply_text}", parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ Ответ отправлен пользователю {user_id}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# =============== АДМИН-ФУНКЦИИ ===============
def change_link(m):
    global SOFT_LINK
    SOFT_LINK = m.text.strip()
    bot.send_message(m.chat.id, f"✅ Ссылка изменена!\n{SOFT_LINK}")

def change_image(m):
    global IMAGE_URL
    IMAGE_URL = m.text.strip()
    bot.send_message(m.chat.id, f"✅ Картинка изменена!")

def give_coins(m):
    try:
        uid, amt = map(int, m.text.split())
        add_coins(uid, amt)
        bot.send_message(m.chat.id, f"✅ Выдано {amt} монет пользователю {uid}\n💰 Баланс: {get_coins(uid)}")
        try:
            bot.send_message(uid, f"💰 Вам начислено {amt} монет! Баланс: {get_coins(uid)}")
        except:
            pass
    except:
        bot.send_message(m.chat.id, "❌ Ошибка! Пример: 123456789 500")

def broadcast(m):
    text = m.text.strip()
    success = fail = 0
    bot.send_message(m.chat.id, "📢 Начинаю рассылку...")
    for uid in users:
        if is_banned(uid): continue
        try:
            bot.send_message(uid, f"📢 Новость:\n{text}")
            success += 1
        except:
            fail += 1
        time.sleep(0.05)
    bot.send_message(m.chat.id, f"✅ Рассылка: {success} доставлено, {fail} ошибок")

def ban_user(m):
    try:
        uid = int(m.text.strip())
        if uid == ADMIN_ID:
            bot.send_message(m.chat.id, "❌ Нельзя забанить админа!")
            return
        blacklist.add(uid)
        save_blacklist()
        bot.send_message(m.chat.id, f"✅ Пользователь {uid} забанен")
        try:
            bot.send_message(uid, "❌ Вы забанены!")
        except:
            pass
    except:
        bot.send_message(m.chat.id, "❌ Ошибка!")

def unban_user(m):
    try:
        uid = int(m.text.strip())
        if uid in blacklist:
            blacklist.remove(uid)
            save_blacklist()
            bot.send_message(m.chat.id, f"✅ Пользователь {uid} разбанен")
            try:
                bot.send_message(uid, "✅ Вы разбанены!")
            except:
                pass
        else:
            bot.send_message(m.chat.id, "❌ Не в ЧС")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка!")

# =============== ОБРАБОТКА ЖАЛОБ ===============
@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_report)
def handle_report(m):
    track_user(m)
    uid = m.from_user.id
    user_name = m.from_user.first_name
    user_username = f"@{m.from_user.username}" if m.from_user.username else "нет username"
    report_text = m.text.strip()
    
    if uid in waiting_for_report:
        del waiting_for_report[uid]
    
    add_coins(uid, 50)
    bot.send_message(uid, "✅ Ваша жалоба отправлена администратору! +50 монет")
    
    admin_message = f"📢 **НОВАЯ ЖАЛОБА!**\n\n"
    admin_message += f"👤 **От:** {user_name}\n"
    admin_message += f"🆔 **ID:** `{uid}`\n"
    admin_message += f"📱 **Username:** {user_username}\n"
    admin_message += f"📝 **Текст жалобы:**\n{report_text}\n"
    admin_message += f"⏰ **Время:** {time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("💬 Ответить пользователю", callback_data=f"reply_{uid}"))
    
    bot.send_message(ADMIN_ID, admin_message, parse_mode="Markdown", reply_markup=keyboard)

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
    load_coins()
    print(f"✅ Загружено: {len(coins_data)} кошельков, {len(message_tracker)} в трекере, {len(blacklist)} в ЧС")
    print(f"✅ Бот запущен! Команды: /start, /buy, /admin, /test")
    
    try:
        bot.send_message(ADMIN_ID, "✅ Бот запущен и работает! Жалобы будут приходить сюда.")
        print("✅ Уведомление админу отправлено")
    except:
        print("⚠️ Админ не начал диалог с ботом! Напишите боту /start, чтобы получать жалобы.")
    
    bot.remove_webhook()
    time.sleep(1)
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'bot-tg-1-x4tg.onrender.com')}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook: {webhook_url}")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
