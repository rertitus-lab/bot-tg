import os
import time
import random
import string
from flask import Flask, request
import telebot
from telebot import types

# =============== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) ===============
TOKEN = "8294974465:AAFfeR0krjHmDUwdQm7rO5N6VfnV8ZvFrOI"  # ⚠️ ЗАМЕНИ НА НОВЫЙ ТОКЕН!
SOFT_LINK = "https://www.mediafire.com/file/aulm7t7mu6388sc/Crack_Sbornik.exe/file"
IMAGE_URL = "https://i.ibb.co/YBXZt30f/ggdoksraz.png"
ADMIN_ID = 7859226148  # ⚠️ ЗАМЕНИ НА СВОЙ ID

# Crack Plus
CRACK_PLUS_LINK = "https://www.mediafire.com/file/fh6v3l9v27jh4g7/crack_plus.exe/file"
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

# =============== ФУНКЦИИ ГЕНЕРАЦИИ КЛЮЧА ===============
def generate_activation_key():
    """Генерирует случайный ключ в формате XXXX-XXXX-XXXX-XXXX"""
    parts = []
    for _ in range(4):
        part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        parts.append(part)
    return '-'.join(parts)

# =============== ФУНКЦИИ ЧЁРНОГО СПИСКА ===============
def load_blacklist():
    global blacklist
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r') as f:
            blacklist = set(int(line.strip()) for line in f if line.strip())
    print(f"✅ Загружен ЧС: {len(blacklist)} пользователей")

def save_blacklist():
    with open(BLACKLIST_FILE, 'w') as f:
        for user_id in blacklist:
            f.write(f"{user_id}\n")

def is_banned(user_id):
    return user_id in blacklist

# =============== ФУНКЦИИ ТРЕКЕРА ===============
def load_messages():
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
    print(f"✅ Загружен трекер: {len(message_tracker)} пользователей")

def save_messages():
    with open(MESSAGE_FILE, 'w') as f:
        for user_id, data in message_tracker.items():
            f.write(f"{user_id}|{data['count']}|{data['username']}|{data['name']}\n")

def update_message_count(user_id, username, first_name):
    if user_id in message_tracker:
        message_tracker[user_id]["count"] += 1
    else:
        message_tracker[user_id] = {"count": 1, "username": username if username else "", "name": first_name}
    save_messages()

# =============== ФУНКЦИИ МОНЕТ ===============
def load_coins():
    global coins_data
    if os.path.exists(COINS_FILE):
        with open(COINS_FILE, 'r') as f:
            for line in f:
                if '|' in line:
                    uid, coins = line.strip().split('|')
                    coins_data[int(uid)] = int(coins)
    print(f"✅ Загружены монеты: {len(coins_data)} пользователей")

def save_coins():
    with open(COINS_FILE, 'w') as f:
        for uid, coins in coins_data.items():
            f.write(f"{uid}|{coins}\n")

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

# =============== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===============
def check_cooldown(user_id):
    now = time.time()
    if user_id in user_last_use:
        passed = now - user_last_use[user_id]
        if passed < 5:
            return int(5 - passed)
    return 0

def update_cooldown(user_id):
    user_last_use[user_id] = time.time()

def is_admin(user_id):
    return user_id == ADMIN_ID

# =============== ДЕКОРАТОР ДЛЯ СЧЁТА ===============
def count_message(func):
    def wrapper(message):
        user_id = message.from_user.id
        username = message.from_user.username or ""
        first_name = message.from_user.first_name
        if user_id != ADMIN_ID:
            update_message_count(user_id, username, first_name)
        return func(message)
    return wrapper

# =============== КОМАНДЫ ===============
@bot.message_handler(commands=['start'])
@count_message
def start(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.send_message(user_id, "❌ Вы забанены!")
        return
    users.add(user_id)
    
    # Начисляем +10 монет за /start
    add_coins(user_id, 10)
    
    cd = check_cooldown(user_id)
    if cd > 0:
        bot.send_message(user_id, f"⏳ Подожди {cd} секунд!")
        return
    update_cooldown(user_id)
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("📥 Скачать софт", callback_data="download"),
        types.InlineKeyboardButton("🎯 Подробнее", callback_data="more"),
        types.InlineKeyboardButton("👥 Поделиться", callback_data="share"),
        types.InlineKeyboardButton("📢 Репорт", callback_data="report"),
        types.InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        types.InlineKeyboardButton("🌐 Crack Plus", callback_data="crack_plus")
    )
    bot.send_message(user_id, "Crack Sbornik - 💥 лучший сборник кряков именно для тебя!", reply_markup=keyboard)

@bot.message_handler(commands=['buy'])
@count_message
def buy_command(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.send_message(user_id, "❌ Вы забанены!")
        return
    
    coins = get_coins(user_id)
    if coins >= CRACK_PLUS_PRICE:
        remove_coins(user_id, CRACK_PLUS_PRICE)
        key = generate_activation_key()
        bot.send_message(user_id, f"👑 **CRACK PLUS АКТИВИРОВАН!**\n\n🔗 Ссылка:\n{CRACK_PLUS_LINK}\n\n🔑 Ваш ключ активации: `{key}`\n\n💰 Остаток монет: {get_coins(user_id)}", parse_mode="Markdown")
    else:
        bot.send_message(user_id, f"❌ У вас не хватает монет! У вас {coins} монет, надо {CRACK_PLUS_PRICE} монет!")

@bot.message_handler(commands=['admin'])
@count_message
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Нет доступа!")
        return
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
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
    bot.send_message(message.chat.id, "🔧 Админ-панель", reply_markup=keyboard)

@bot.message_handler(commands=['cancel'])
@count_message
def cancel_report(message):
    user_id = message.from_user.id
    if user_id in waiting_for_report:
        del waiting_for_report[user_id]
        bot.reply_to(message, "❌ Отправка жалобы отменена")
    else:
        bot.reply_to(message, "❌ Нет активной жалобы")

# =============== КНОПКИ ПОЛЬЗОВАТЕЛЯ ===============
@bot.callback_query_handler(func=lambda call: call.data == "download")
def download_callback(call):
    user_id = call.from_user.id
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    cd = check_cooldown(user_id)
    if cd > 0:
        bot.answer_callback_query(call.id, f"⏳ {cd} сек!", True)
        return
    update_cooldown(user_id)
    global download_count
    download_count += 1
    bot.answer_callback_query(call.id, "✅ Ссылка отправлена!", False)
    bot.send_message(user_id, f"🔗 Ссылка:\n{SOFT_LINK}")

@bot.callback_query_handler(func=lambda call: call.data == "more")
def more_callback(call):
    user_id = call.from_user.id
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    cd = check_cooldown(user_id)
    if cd > 0:
        bot.answer_callback_query(call.id, f"⏳ {cd} сек!", True)
        return
    update_cooldown(user_id)
    bot.answer_callback_query(call.id, "📸", False)
    bot.send_photo(user_id, IMAGE_URL, caption="☢️ антивирус может ругаться на софт потому что это кряк ☢️")

@bot.callback_query_handler(func=lambda call: call.data == "share")
def share_callback(call):
    user_id = call.from_user.id
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(user_id, f"👥 Поделиться:\nhttps://t.me/{bot.get_me().username}")

@bot.callback_query_handler(func=lambda call: call.data == "report")
def report_callback(call):
    user_id = call.from_user.id
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    cd = check_cooldown(user_id)
    if cd > 0:
        bot.answer_callback_query(call.id, f"⏳ {cd} сек!", True)
        return
    update_cooldown(user_id)
    bot.answer_callback_query(call.id)
    waiting_for_report[user_id] = True
    bot.send_message(user_id, "⚙️ Напишите текст жалобы (/cancel для отмены)")

@bot.callback_query_handler(func=lambda call: call.data == "balance")
def balance_callback(call):
    user_id = call.from_user.id
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    bot.answer_callback_query(call.id)
    coins = get_coins(user_id)
    bot.send_message(user_id, f"💰 Ваш баланс: {coins} монет")

@bot.callback_query_handler(func=lambda call: call.data == "crack_plus")
def crack_plus_callback(call):
    user_id = call.from_user.id
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    cd = check_cooldown(user_id)
    if cd > 0:
        bot.answer_callback_query(call.id, f"⏳ {cd} сек!", True)
        return
    update_cooldown(user_id)
    bot.answer_callback_query(call.id)
    bot.send_message(user_id, "Напишите /buy чтобы купить Crack Plus!\n\nКоманда /start дает +10 монет к балансу!\n\nCrack Plus дает лучшую оптимизацию, гибкие настройки и больше функций!")

# =============== ОБРАБОТКА ЖАЛОБ ===============
@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_report)
def process_report(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_username = f"@{message.from_user.username}" if message.from_user.username else "нет username"
    report_text = message.text.strip()
    username = message.from_user.username or ""
    first_name = message.from_user.first_name
    if user_id != ADMIN_ID:
        update_message_count(user_id, username, first_name)
    try:
        bot.send_chat_action(ADMIN_ID, 'typing')
    except:
        bot.reply_to(message, "⚠️ Админ не начал диалог с ботом")
        if user_id in waiting_for_report:
            del waiting_for_report[user_id]
        return
    admin_message = f"📢 НОВАЯ ЖАЛОБА!\n👤 От: {user_name}\n🆔 ID: {user_id}\n📱 Username: {user_username}\n📝 Текст: {report_text}\n⏰ Время: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    bot.send_message(ADMIN_ID, admin_message)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{user_id}"))
    bot.send_message(ADMIN_ID, "🔧 Действия:", reply_markup=keyboard)
    bot.reply_to(message, "✅ Жалоба отправлена!")
    if user_id in waiting_for_report:
        del waiting_for_report[user_id]

# =============== ОТВЕТ ПОЛЬЗОВАТЕЛЮ ===============
@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def reply_to_user(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    user_id = int(call.data.split('_')[1])
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"✏️ Введите ответ для пользователя (ID: {user_id}):")
    bot.register_next_step_handler(msg, lambda m: send_reply(m, user_id))

def send_reply(message, user_id):
    reply_text = message.text.strip()
    try:
        bot.send_message(user_id, f"📢 Ответ администратора:\n{reply_text}")
        bot.send_message(message.chat.id, f"✅ Ответ отправлен")
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
    bot.send_message(m.chat.id, f"✅ Картинка изменена!\n{IMAGE_URL}")

def broadcast_msg(m):
    text = m.text.strip()
    success = fail = 0
    bot.send_message(m.chat.id, "📢 Начинаю рассылку...")
    for uid in users:
        if is_banned(uid):
            continue
        try:
            bot.send_message(uid, f"📢 Новость:\n{text}")
            success += 1
        except:
            fail += 1
        time.sleep(0.05)
    bot.send_message(m.chat.id, f"✅ Рассылка завершена!\n📨 Доставлено: {success}\n❌ Ошибок: {fail}")

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
        bot.send_message(m.chat.id, "❌ Ошибка! Введите ID")

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
            bot.send_message(m.chat.id, f"❌ Пользователь {uid} не в ЧС")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка! Введите ID")

# =============== ВЫДАЧА МОНЕТ (АДМИН) ===============
@bot.callback_query_handler(func=lambda call: call.data == "admin_give_coins")
def give_coins_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💰 Введите ID пользователя и сумму монет через пробел\n\nПример: `123456789 500`\nСумма от 1 до 100000", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_give_coins)

def process_give_coins(message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ Ошибка! Введите ID и сумму через пробел\nПример: `123456789 500`", parse_mode="Markdown")
            return
        user_id = int(parts[0])
        amount = int(parts[1])
        if amount < 1 or amount > 100000:
            bot.send_message(message.chat.id, "❌ Сумма должна быть от 1 до 100000 монет!")
            return
        add_coins(user_id, amount)
        bot.send_message(message.chat.id, f"✅ Пользователю `{user_id}` выдано {amount} монет!\n💰 Баланс: {get_coins(user_id)}", parse_mode="Markdown")
        try:
            bot.send_message(user_id, f"💰 Вам начислено {amount} монет!\n💰 Ваш баланс: {get_coins(user_id)}")
        except:
            pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ Ошибка! Введите ID (число) и сумму (число)")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# =============== АДМИН-КНОПКИ ===============
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_') and call.data != "admin_give_coins")
def admin_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    if call.data == "admin_stats":
        bot.send_message(call.message.chat.id, f"📊 Статистика:\n📥 Скачиваний: {download_count}\n👥 Пользователей: {len(users)}")
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
        bot.register_next_step_handler(msg, broadcast_msg)
    elif call.data == "admin_ban":
        msg = bot.send_message(call.message.chat.id, "🚫 Введите ID для бана:")
        bot.register_next_step_handler(msg, ban_user)
    elif call.data == "admin_unban":
        msg = bot.send_message(call.message.chat.id, "✅ Введите ID для разбана:")
        bot.register_next_step_handler(msg, unban_user)
    elif call.data == "admin_banlist":
        if blacklist:
            lst = "\n".join([str(uid) for uid in blacklist])
            bot.send_message(call.message.chat.id, f"📋 Забаненные:\n{lst}")
        else:
            bot.send_message(call.message.chat.id, "📋 ЧС пуст")
    elif call.data == "admin_tracker":
        if not message_tracker:
            bot.send_message(call.message.chat.id, "📊 Нет данных")
            return
        sorted_users = sorted(message_tracker.items(), key=lambda x: x[1]["count"], reverse=True)[:20]
        text = "📊 Топ по сообщениям:\n"
        for i, (uid, data) in enumerate(sorted_users, 1):
            name = data.get('username') or data.get('name', str(uid))[:15]
            text += f"{i}. {name} — {data['count']}\n"
        bot.send_message(call.message.chat.id, text)

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
    bot.remove_webhook()
    time.sleep(1)
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'bot-tg-1-x4tg.onrender.com')}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook: {webhook_url}")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
