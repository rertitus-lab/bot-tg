import os
import time
import random
import string
from flask import Flask, request
import telebot
from telebot import types

# =============== НАСТРОЙКИ ===============
TOKEN = "8294974465:AAFfeR0krjHmDUwdQm7rO5N6VfnV8ZvFrOI"  # ⚠️ ЗАМЕНИ
ADMIN_ID = 7859226148

SOFT_LINK = "https://www.mediafire.com/file/giyvpt6yuy9so7m/Crack_Sbornik.exe/file"
IMAGE_URL = "https://i.ibb.co/YBXZt30f/ggdoksraz.png"
CRACK_PLUS_LINK = "https://www.mediafire.com/file/2w6a3y18ke8vr94/Crack_Plus.exe/file"
CRACK_PLUS_PRICE = 2500

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

def generate_key():
    parts = []
    for _ in range(4):
        part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        parts.append(part)
    return '-'.join(parts)

def load_blacklist():
    global blacklist
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r') as f:
            blacklist = set(int(line.strip()) for line in f if line.strip())

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

def save_coins():
    with open(COINS_FILE, 'w') as f:
        for uid, val in coins_data.items():
            f.write(f"{uid}|{val}\n")

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
        types.InlineKeyboardButton("🌐 Crack Plus", callback_data="crack_plus"),
        types.InlineKeyboardButton("🎰 Колесо фортуны", callback_data="fortune_wheel"),
        types.InlineKeyboardButton("📦 Кейсы", callback_data="cases_menu")
    )
    bot.send_message(uid, "Crack Sbornik - 💥 лучший сборник кряков именно для тебя!", reply_markup=kb)

@bot.message_handler(commands=['admin'])
def admin(m):
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
    uid = m.from_user.id
    if uid in waiting_for_report:
        del waiting_for_report[uid]
        bot.reply_to(m, "❌ Отменено")

# =============== МЕНЮ КЕЙСОВ ===============
@bot.callback_query_handler(func=lambda call: call.data == "cases_menu")
def cases_menu(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    bot.answer_callback_query(call.id)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🥉 Бронзовый кейс (25)", callback_data="case_bronze"),
        types.InlineKeyboardButton("🥈 Серебряный кейс (300)", callback_data="case_silver"),
        types.InlineKeyboardButton("💎 Легендарный кейс (1250)", callback_data="case_legendary"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")
    )
    bot.send_message(uid, "📦 **Выбери кейс:**", parse_mode="Markdown", reply_markup=kb)

# =============== КЕЙСЫ (ГЛАВНАЯ ФУНКЦИЯ) ===============
@bot.callback_query_handler(func=lambda call: call.data in ["case_bronze", "case_silver", "case_legendary"])
def open_case(call):
    uid = call.from_user.id
    
    # Определяем параметры кейса
    if call.data == "case_bronze":
        price = 25
        win_chance = 10
    elif call.data == "case_silver":
        price = 300
        win_chance = 25
    else:  # case_legendary
        price = 1250
        win_chance = 45
    
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    
    coins = get_coins(uid)
    if coins < price:
        bot.answer_callback_query(call.id, f"❌ Нужно {price} монет! У тебя {coins}", True)
        return
    
    # Открываем кейс
    bot.answer_callback_query(call.id, "🎲 Открываем кейс...")
    remove_coins(uid, price)
    
    rand = random.randint(1, 100)
    
    # ВЫИГРЫШ CRACK PLUS
    if rand <= win_chance:
        key = generate_key()
        bot.send_message(uid, f"🎉 **ВЫ ВЫИГРАЛИ CRACK PLUS!** 🎉\n\n🔗 Ссылка:\n{CRACK_PLUS_LINK}\n\n🔑 Ключ активации: `{key}`\n\n💰 Остаток монет: {get_coins(uid)}", parse_mode="Markdown")
    else:
        # ПРОИГРЫШ
        if call.data == "case_bronze":
            bot.send_message(uid, f"😔 **Вам ничего не выпало!**\n\n💰 Потеряно: {price} монет\n💰 Остаток: {get_coins(uid)}")
        elif call.data == "case_silver":
            add_coins(uid, 100)
            bot.send_message(uid, f"🎁 **Вы выиграли 100 монет!**\n\n💰 Новый баланс: {get_coins(uid)}")
        else:
            add_coins(uid, 125)
            bot.send_message(uid, f"🎁 **Вы выиграли 125 монет!**\n\n💰 Новый баланс: {get_coins(uid)}")
    
    # Кнопки для продолжения
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🥉 Бронзовый (25)", callback_data="case_bronze"),
        types.InlineKeyboardButton("🥈 Серебряный (300)", callback_data="case_silver"),
        types.InlineKeyboardButton("💎 Легендарный (1250)", callback_data="case_legendary"),
        types.InlineKeyboardButton("🔙 В меню", callback_data="cases_menu")
    )
    bot.send_message(uid, "Хочешь открыть ещё кейс?", reply_markup=kb)

# =============== КНОПКА НАЗАД ===============
@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📥 Скачать софт", callback_data="download"),
        types.InlineKeyboardButton("🎯 Подробнее", callback_data="more"),
        types.InlineKeyboardButton("👥 Поделиться", callback_data="share"),
        types.InlineKeyboardButton("📢 Репорт", callback_data="report"),
        types.InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        types.InlineKeyboardButton("🌐 Crack Plus", callback_data="crack_plus"),
        types.InlineKeyboardButton("🎰 Колесо фортуны", callback_data="fortune_wheel"),
        types.InlineKeyboardButton("📦 Кейсы", callback_data="cases_menu")
    )
    bot.send_message(uid, "Crack Sbornik - 💥 лучший сборник кряков именно для тебя!", reply_markup=kb)

# =============== КОЛЕСО ФОРТУНЫ ===============
@bot.callback_query_handler(func=lambda call: call.data == "fortune_wheel")
def fortune_menu(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    coins = get_coins(uid)
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🎲 10", callback_data="fortune_10"),
        types.InlineKeyboardButton("🎲 50", callback_data="fortune_50"),
        types.InlineKeyboardButton("🎲 100", callback_data="fortune_100"),
        types.InlineKeyboardButton("🎲 300", callback_data="fortune_300"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")
    )
    bot.answer_callback_query(call.id)
    bot.send_message(uid, f"🎰 Колесо фортуны\n💰 Баланс: {coins}", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("fortune_"))
def fortune_spin(call):
    uid = call.from_user.id
    bet = int(call.data.split('_')[1])
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    coins = get_coins(uid)
    if coins < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet} монет!", True)
        return
    bot.answer_callback_query(call.id, "🎰 Крутим...")
    is_win = random.choice([True, False])
    if is_win:
        if bet == 10: prizes = [10, 20, 50, 100]
        elif bet == 50: prizes = [50, 100, 150, 250]
        elif bet == 100: prizes = [100, 200, 300, 500]
        else: prizes = [300, 600, 900, 1500]
        win = random.choice(prizes)
        remove_coins(uid, bet)
        add_coins(uid, win)
        bot.send_message(uid, f"🎉 ПОБЕДА!\n💰 Ставка: {bet}\n🏆 Выигрыш: {win}\n💰 Новый баланс: {get_coins(uid)}")
    else:
        remove_coins(uid, bet)
        bot.send_message(uid, f"😔 ПРОИГРЫШ!\n💰 Потеряно: {bet}\n💰 Новый баланс: {get_coins(uid)}")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🎰 Ещё", callback_data="fortune_wheel"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu"))
    bot.send_message(uid, "Хочешь сыграть ещё?", reply_markup=kb)

# =============== ОБЫЧНЫЕ КНОПКИ ===============
@bot.callback_query_handler(func=lambda call: call.data in ["download", "more", "share", "balance", "crack_plus", "report"])
def simple_buttons(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    
    cd = check_cd(uid)
    if cd > 0:
        bot.answer_callback_query(call.id, f"⏳ {cd} сек!", True)
        return
    update_cd(uid)
    
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
        bot.send_message(uid, f"👥 Поделиться: https://t.me/{bot.get_me().username}")
    elif call.data == "balance":
        bot.answer_callback_query(call.id)
        bot.send_message(uid, f"💰 Баланс: {get_coins(uid)} монет")
    elif call.data == "crack_plus":
        bot.answer_callback_query(call.id)
        bot.send_message(uid, "🌐 Crack Plus\nНапишите /buy чтобы купить!")
    elif call.data == "report":
        waiting_for_report[uid] = True
        bot.answer_callback_query(call.id)
        bot.send_message(uid, "✍️ Напишите текст жалобы (/cancel для отмены)")

# =============== ПОКУПКА CRACK PLUS ===============
@bot.message_handler(commands=['buy'])
def buy(m):
    uid = m.from_user.id
    if is_banned(uid):
        bot.send_message(uid, "❌ Вы забанены!")
        return
    coins = get_coins(uid)
    if coins >= CRACK_PLUS_PRICE:
        remove_coins(uid, CRACK_PLUS_PRICE)
        key = generate_key()
        bot.send_message(uid, f"🎉 CRACK PLUS КУПЛЕН!\n\n🔗 {CRACK_PLUS_LINK}\n\n🔑 Ключ: {key}\n💰 Остаток: {get_coins(uid)}")
    else:
        bot.send_message(uid, f"❌ Нужно {CRACK_PLUS_PRICE} монет! У вас {coins}")

# =============== АДМИН-ФУНКЦИИ ===============
def change_link(m):
    global SOFT_LINK
    SOFT_LINK = m.text.strip()
    bot.send_message(m.chat.id, f"✅ Ссылка изменена!")

def change_image(m):
    global IMAGE_URL
    IMAGE_URL = m.text.strip()
    bot.send_message(m.chat.id, f"✅ Картинка изменена!")

def give_coins(m):
    try:
        uid, amt = map(int, m.text.split())
        add_coins(uid, amt)
        bot.send_message(m.chat.id, f"✅ Выдано {amt} монет\n💰 Баланс: {get_coins(uid)}")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка! Пример: 123456789 500")

def broadcast(m):
    text = m.text.strip()
    success = fail = 0
    for uid in users:
        if is_banned(uid): continue
        try:
            bot.send_message(uid, f"📢 {text}")
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

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_buttons(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    
    if call.data == "admin_stats":
        bot.send_message(call.message.chat.id, f"📊 Статистика:\n📥 Скачиваний: {download_count}\n👥 Пользователей: {len(users)}")
    elif call.data == "admin_users":
        bot.send_message(call.message.chat.id, f"👥 Пользователей: {len(users)}")
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
        msg = bot.send_message(call.message.chat.id, "🚫 Введите ID:")
        bot.register_next_step_handler(msg, ban_user)
    elif call.data == "admin_unban":
        msg = bot.send_message(call.message.chat.id, "✅ Введите ID:")
        bot.register_next_step_handler(msg, unban_user)
    elif call.data == "admin_banlist":
        if blacklist:
            bot.send_message(call.message.chat.id, f"📋 Забаненные:\n" + "\n".join(str(x) for x in blacklist))
        else:
            bot.send_message(call.message.chat.id, "📋 ЧС пуст")
    elif call.data == "admin_tracker":
        if not message_tracker:
            bot.send_message(call.message.chat.id, "📊 Нет данных")
            return
        top = sorted(message_tracker.items(), key=lambda x: x[1]["count"], reverse=True)[:20]
        text = "📊 Топ по сообщениям:\n"
        for i, (uid, d) in enumerate(top, 1):
            name = d.get('username') or d.get('name', str(uid))[:15]
            text += f"{i}. {name} — {d['count']}\n"
        bot.send_message(call.message.chat.id, text)
    elif call.data == "admin_give_coins":
        msg = bot.send_message(call.message.chat.id, "💰 Введите: ID количество")
        bot.register_next_step_handler(msg, give_coins)

# =============== ЖАЛОБЫ ===============
@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_report)
def handle_report(m):
    uid = m.from_user.id
    text = m.text.strip()
    if uid in waiting_for_report:
        del waiting_for_report[uid]
    add_coins(uid, 50)
    bot.send_message(uid, "✅ Жалоба отправлена! +50 монет")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{uid}"))
    bot.send_message(ADMIN_ID, f"📢 ЖАЛОБА от {m.from_user.first_name} (ID: {uid})\nТекст: {text}", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def reply_to_user(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    uid = int(call.data.split('_')[1])
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"Введите ответ для {uid}:")
    bot.register_next_step_handler(msg, lambda m: send_reply(m, uid))

def send_reply(m, uid):
    try:
        bot.send_message(uid, f"📢 Ответ администратора:\n\n{m.text.strip()}")
        bot.send_message(m.chat.id, "✅ Ответ отправлен")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка")

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
    print("✅ Бот запущен!")
    bot.remove_webhook()
    time.sleep(1)
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'bot-tg-1-x4tg.onrender.com')}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
