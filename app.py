import os
import time
import random
import string
import threading
import json
from flask import Flask, request
import telebot
from telebot import types

# =============== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) ===============
TOKEN = "8640251515:AAGSSw5fBnljGfXa8yK1QwTIDcv-lckYUp4"
ADMIN_ID = 7859226148

SOFT_LINK = "https://www.mediafire.com/file/giyvpt6yuy9so7m/Crack_Sbornik.exe/file"
IMAGE_URL = "https://i.ibb.co/YBXZt30f/ggdoksraz.png"
CRACK_PLUS_LINK = "https://www.mediafire.com/file/2w6a3y18ke8vr94/Crack_Plus.exe/file"
CRACK_PLUS_PRICE = 60000

# =============== СТАТУСЫ ===============
STATUS_INFO = {
    "🟢 Новичок": {"price": 0, "bonus": 1.0, "no_cd": False},
    "🔵 Продвинутый": {"price": 1000, "bonus": 1.1, "no_cd": False},
    "🟣 Опытный": {"price": 5000, "bonus": 1.2, "no_cd": False},
    "🟠 Эксперт": {"price": 20000, "bonus": 1.3, "no_cd": False},
    "🔴 Мастер": {"price": 50000, "bonus": 1.5, "no_cd": True},
    "👑 Бог": {"price": 100000, "bonus": 1.75, "no_cd": True},
    "👑 Герцог": {"price": 2500000, "bonus": 3.0, "no_cd": True}
}

# Настройки Герцога
duke_settings = {}
DUKE_SETTINGS_FILE = "duke_settings.txt"

# Магазин
MARKET_ITEMS = {
    "status_🔵 Продвинутый": {"price": 1000, "type": "status", "bonus": 1.1, "no_cd": False},
    "status_🟣 Опытный": {"price": 5000, "type": "status", "bonus": 1.2, "no_cd": False},
    "status_🟠 Эксперт": {"price": 20000, "type": "status", "bonus": 1.3, "no_cd": False},
    "status_🔴 Мастер": {"price": 50000, "type": "status", "bonus": 1.5, "no_cd": True},
    "status_👑 Бог": {"price": 100000, "type": "status", "bonus": 1.75, "no_cd": True},
    "status_👑 Герцог": {"price": 2500000, "type": "status", "bonus": 3.0, "no_cd": True},
}

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
ttt_games = {}
user_stats = {}
user_boosts = {}
user_permanent = {}

BLACKLIST_FILE = "blacklist.txt"
MESSAGE_FILE = "messages.txt"
COINS_FILE = "coins.txt"
STATS_FILE = "user_stats.txt"
BOOSTS_FILE = "boosts.txt"
PERMANENT_FILE = "permanent.txt"

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
    print(f"✅ Загружен ЧС: {len(blacklist)}")

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
    print(f"✅ Загружен трекер: {len(message_tracker)}")

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
    print(f"✅ Загружены монеты: {len(coins_data)}")

def save_coins():
    with open(COINS_FILE, 'w') as f:
        for uid, val in coins_data.items():
            f.write(f"{uid}|{val}\n")

def load_stats():
    global user_stats
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            for line in f:
                if '|' in line:
                    parts = line.strip().split('|')
                    if len(parts) >= 7:
                        uid = int(parts[0])
                        user_stats[uid] = {
                            "admin_give": int(parts[3]),
                            "admin_take": int(parts[4]),
                            "fortune_win": int(parts[5]),
                            "ttt_win": int(parts[6]) if len(parts) > 6 else 0,
                            "download": int(parts[7]) if len(parts) > 7 else 0,
                            "report": int(parts[8]) if len(parts) > 8 else 0,
                            "total_earned": int(parts[9]) if len(parts) > 9 else 0,
                            "status": parts[10] if len(parts) > 10 else "",
                            "title": parts[11] if len(parts) > 11 else ""
                        }
    print(f"✅ Загружена статистика: {len(user_stats)}")

def save_stats():
    with open(STATS_FILE, 'w') as f:
        for uid, data in user_stats.items():
            f.write(f"{uid}|{uid}|{uid}|{data['admin_give']}|{data['admin_take']}|{data['fortune_win']}|{data['ttt_win']}|{data['download']}|{data['report']}|{data['total_earned']}|{data.get('status', '')}|{data.get('title', '')}\n")

def update_user_stat(uid, stat_name, amount):
    if uid not in user_stats:
        user_stats[uid] = {
            "admin_give": 0, "admin_take": 0, "fortune_win": 0, "ttt_win": 0,
            "download": 0, "report": 0, "total_earned": 0, "status": "", "title": ""
        }
    if stat_name in user_stats[uid]:
        user_stats[uid][stat_name] += amount
    save_stats()

def update_total_earned(uid, amount):
    if uid not in user_stats:
        user_stats[uid] = {
            "admin_give": 0, "admin_take": 0, "fortune_win": 0, "ttt_win": 0,
            "download": 0, "report": 0, "total_earned": 0, "status": "", "title": ""
        }
    user_stats[uid]["total_earned"] += amount
    save_stats()

def get_total_earned(uid):
    return user_stats.get(uid, {}).get("total_earned", 0)

def get_status_and_bonus(uid):
    if uid in user_stats and user_stats[uid].get("status"):
        manual_status = user_stats[uid]["status"]
        for status, data in STATUS_INFO.items():
            if status == manual_status:
                return manual_status, data["bonus"]
        return manual_status, 1.0
    total = get_total_earned(uid)
    for status, data in STATUS_INFO.items():
        if data["price"] <= total:
            return status, data["bonus"]
    return "🟢 Новичок", 1.0

# =============== БУСТЫ И ПЕРМАНЕНТЫ ===============
def load_boosts():
    global user_boosts
    if os.path.exists(BOOSTS_FILE):
        with open(BOOSTS_FILE, 'r') as f:
            user_boosts = json.load(f)

def save_boosts():
    with open(BOOSTS_FILE, 'w') as f:
        json.dump(user_boosts, f)

def load_permanent():
    global user_permanent
    if os.path.exists(PERMANENT_FILE):
        with open(PERMANENT_FILE, 'r') as f:
            user_permanent = json.load(f)

def save_permanent():
    with open(PERMANENT_FILE, 'w') as f:
        json.dump(user_permanent, f)

def load_duke_settings():
    global duke_settings
    if os.path.exists(DUKE_SETTINGS_FILE):
        with open(DUKE_SETTINGS_FILE, 'r') as f:
            duke_settings = json.load(f)

def save_duke_settings():
    with open(DUKE_SETTINGS_FILE, 'w') as f:
        json.dump(duke_settings, f)

# =============== ВСПОМОГАТЕЛЬНЫЕ ===============
def is_banned(uid): return uid in blacklist
def is_admin(uid): return uid == ADMIN_ID
def get_coins(uid): return coins_data.get(uid, 0)
def add_coins(uid, amt): 
    coins_data[uid] = get_coins(uid) + amt
    save_coins()

def add_coins_with_bonus(uid, amount, source):
    status, bonus = get_status_and_bonus(uid)
    bonus_amount = int(amount * bonus)
    add_coins(uid, bonus_amount)
    update_user_stat(uid, source, amount)
    update_total_earned(uid, bonus_amount)
    return bonus_amount

def remove_coins(uid, amt):
    if get_coins(uid) >= amt:
        coins_data[uid] -= amt
        save_coins()
        return True
    return False

def check_cd(uid):
    status, _ = get_status_and_bonus(uid)
    if STATUS_INFO.get(status, {}).get("no_cd", False):
        return 0
    now = time.time()
    if uid in user_last_use and now - user_last_use[uid] < 5:
        return int(5 - (now - user_last_use[uid]))
    return 0

def update_cd(uid):
    user_last_use[uid] = time.time()

def track_user(message):
    uid = message.from_user.id
    update_message_count(uid, message.from_user.username or "", message.from_user.first_name)

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
    update_user_stat(uid, "download", 1)
    bot.answer_callback_query(call.id, "✅ Ссылка отправлена!")
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
    bot.answer_callback_query(call.id, "📸")
    bot.send_photo(uid, IMAGE_URL, caption="☢️ антивирус может ругаться")

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
    waiting_for_report[uid] = True
    bot.answer_callback_query(call.id)
    bot.send_message(uid, "✍️ Напишите текст жалобы (/cancel для отмены)")

@bot.callback_query_handler(func=lambda call: call.data == "crack_plus")
def crack_plus_callback(call):
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
    bot.send_message(uid, "🌐 **Crack Plus**\n\n💲 цена 60000 монет\n\nНапишите /buy чтобы купить!", parse_mode="Markdown")

# =============== КРЕСТИКИ-НОЛИКИ ===============
def create_ttt_keyboard(board):
    kb = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for i in range(9):
        emoji = "❌" if board[i] == "X" else "⭕" if board[i] == "O" else "⬜"
        buttons.append(types.InlineKeyboardButton(emoji, callback_data=f"ttt_{i}"))
    kb.add(*buttons)
    return kb

def check_winner(board):
    win_patterns = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    for pattern in win_patterns:
        if board[pattern[0]] == board[pattern[1]] == board[pattern[2]] != "":
            return board[pattern[0]]
    if "" not in board:
        return "draw"
    return None

def bot_move_duke(board, uid):
    status, _ = get_status_and_bonus(uid)
    if status == "👑 Герцог":
        if random.random() < 0.3:
            free_cells = [i for i in range(9) if board[i] == ""]
            if free_cells:
                return random.choice(free_cells)
    free_cells = [i for i in range(9) if board[i] == ""]
    if free_cells:
        return random.choice(free_cells)
    return None

def format_board_for_message(board):
    symbols = {"X": "❌", "O": "⭕", "": "⬜"}
    rows = []
    for i in range(0, 9, 3):
        row = " ".join(symbols[board[j]] for j in range(i, i+3))
        rows.append(row)
    return "```\n" + "\n".join(rows) + "\n```"

def game_over_message(winner, board, bet):
    win_amount = bet * 2
    if winner == "X":
        return f"🎉 **ПОБЕДА!** 🎉\n\nТы выиграл {win_amount} монет (x2 от {bet})!\n\n" + format_board_for_message(board)
    elif winner == "O":
        return f"😔 **ПРОИГРЫШ!** 😔\n\nТы проиграл {bet} монет.\n\n" + format_board_for_message(board)
    else:
        return f"🤝 **НИЧЬЯ!** 🤝\n\nСтавка возвращена — {bet} монет.\n\n" + format_board_for_message(board)

@bot.callback_query_handler(func=lambda call: call.data == "tic_tac_toe")
def tic_tac_toe_menu(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🎲 50 монет", callback_data="ttt_bet_50"),
        types.InlineKeyboardButton("🎲 100 монет", callback_data="ttt_bet_100"),
        types.InlineKeyboardButton("🎲 300 монет", callback_data="ttt_bet_300"),
        types.InlineKeyboardButton("🎲 1000 монет", callback_data="ttt_bet_1000"),
        types.InlineKeyboardButton("🎲 2000 монет", callback_data="ttt_bet_2000"),
        types.InlineKeyboardButton("🎲 10000 монет", callback_data="ttt_bet_10000"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")
    )
    bot.answer_callback_query(call.id)
    bot.send_message(uid, "❌ **Крестики-нолики**\n\nВыбери ставку (при победе x2):", parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ttt_bet_"))
def start_ttt_game(call):
    uid = call.from_user.id
    bet = int(call.data.split('_')[2])
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    coins = get_coins(uid)
    if coins < bet:
        bot.answer_callback_query(call.id, f"❌ Не хватает монет! Нужно {bet}, у тебя {coins}", True)
        return
    bot.answer_callback_query(call.id)
    board = [""] * 9
    remove_coins(uid, bet)
    ttt_games[uid] = {"board": board, "turn": "user", "bet": bet, "message_id": None, "chat_id": call.message.chat.id}
    kb = create_ttt_keyboard(board)
    msg = bot.send_message(uid, f"❌ **Крестики-нолики**\n\n💰 Ставка: {bet} монет\n💰 Выигрыш: {bet * 2} монет (x2)\nТвой ход (❌):\n\n{format_board_for_message(board)}", parse_mode="Markdown", reply_markup=kb)
    ttt_games[uid]["message_id"] = msg.message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith("ttt_") and not call.data.startswith("ttt_bet_"))
def ttt_move(call):
    uid = call.from_user.id
    cell = int(call.data.split('_')[1])
    if uid not in ttt_games:
        bot.answer_callback_query(call.id, "❌ Игра не найдена!", True)
        return
    game = ttt_games[uid]
    board = game["board"]
    chat_id = game["chat_id"]
    message_id = game["message_id"]
    bet = game["bet"]
    if game["turn"] != "user":
        bot.answer_callback_query(call.id, "⏳ Сейчас ход бота!", True)
        return
    if board[cell] != "":
        bot.answer_callback_query(call.id, "❌ Эта клетка уже занята!", True)
        return
    board[cell] = "X"
    winner = check_winner(board)
    if winner == "X":
        win_amount = bet * 2
        final_amount = add_coins_with_bonus(uid, win_amount, "ttt_win")
        bot.edit_message_text(game_over_message("X", board, bet), chat_id, message_id, parse_mode="Markdown")
        del ttt_games[uid]
        bot.answer_callback_query(call.id, f"🎉 Выиграл {final_amount} монет!", show_alert=True)
        return
    elif winner == "draw":
        add_coins(uid, bet)
        bot.edit_message_text(game_over_message("draw", board, bet), chat_id, message_id, parse_mode="Markdown")
        del ttt_games[uid]
        bot.answer_callback_query(call.id, f"🤝 Ничья! Возвращено {bet} монет", show_alert=True)
        return
    game["turn"] = "bot"
    bot.answer_callback_query(call.id, "🤖 Бот думает...")
    kb = create_ttt_keyboard(board)
    bot.edit_message_text(f"❌ **Крестики-нолики**\n\n💰 Ставка: {bet} монет\n💰 Выигрыш: {bet * 2} монет (x2)\nХод бота (⭕):\n\n{format_board_for_message(board)}", chat_id, message_id, parse_mode="Markdown", reply_markup=kb)
    
    def bot_move_async():
        time.sleep(1)
        move = bot_move_duke(board, uid)
        if move is not None:
            board[move] = "O"
        winner = check_winner(board)
        if winner == "O":
            bot.edit_message_text(game_over_message("O", board, bet), chat_id, message_id, parse_mode="Markdown")
            del ttt_games[uid]
            bot.answer_callback_query(call.id, f"😔 Проиграл {bet} монет", show_alert=True)
        elif winner == "draw":
            add_coins(uid, bet)
            bot.edit_message_text(game_over_message("draw", board, bet), chat_id, message_id, parse_mode="Markdown")
            del ttt_games[uid]
            bot.answer_callback_query(call.id, f"🤝 Ничья! Возвращено {bet} монет", show_alert=True)
        else:
            game["turn"] = "user"
            kb = create_ttt_keyboard(board)
            bot.edit_message_text(f"❌ **Крестики-нолики**\n\n💰 Ставка: {bet} монет\n💰 Выигрыш: {bet * 2} монет (x2)\nТвой ход (❌):\n\n{format_board_for_message(board)}", chat_id, message_id, parse_mode="Markdown", reply_markup=kb)
    
    threading.Thread(target=bot_move_async).start()

# =============== КОЛЕСО ФОРТУНЫ ===============
@bot.callback_query_handler(func=lambda call: call.data == "fortune_wheel")
def fortune_wheel_menu(call):
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
        types.InlineKeyboardButton("🎲 5000", callback_data="fortune_5000"),
        types.InlineKeyboardButton("🎲 10000", callback_data="fortune_10000"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")
    )
    bot.answer_callback_query(call.id)
    bot.send_message(uid, f"🎰 **Колесо фортуны**\n💰 Баланс: {coins}\nВыбери ставку (50% победа):", parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("fortune_"))
def fortune_spin(call):
    uid = call.from_user.id
    bet = int(call.data.split('_')[1])
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    coins = get_coins(uid)
    if coins < bet:
        bot.answer_callback_query(call.id, f"❌ Нужно {bet}, у тебя {coins}", True)
        return
    bot.answer_callback_query(call.id, "🎰 Крутится...")
    
    status, _ = get_status_and_bonus(uid)
    if status == "👑 Герцог":
        is_win = random.random() < 0.8
    else:
        is_win = random.choice([True, False])
    
    if is_win:
        if bet == 10: prizes = [10, 20, 50, 100]
        elif bet == 50: prizes = [50, 100, 150, 250]
        elif bet == 100: prizes = [100, 200, 300, 500]
        elif bet == 300: prizes = [300, 600, 900, 1500]
        elif bet == 5000: prizes = [5000, 10000, 15000, 20000]
        else: prizes = [10000, 20000, 30000, 40000]
        win = random.choice(prizes)
        remove_coins(uid, bet)
        add_coins_with_bonus(uid, win, "fortune_win")
        bot.send_message(uid, f"🎉 **ПОБЕДА!**\n💰 Ставка: {bet}\n🏆 Выигрыш: {win}\n💰 Новый баланс: {get_coins(uid)}", parse_mode="Markdown")
    else:
        remove_coins(uid, bet)
        bot.send_message(uid, f"😔 **ПРОИГРЫШ!**\n💰 Потеряно: {bet}\n💰 Новый баланс: {get_coins(uid)}", parse_mode="Markdown")
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🎰 Ещё", callback_data="fortune_wheel"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu"))
    bot.send_message(uid, "Хочешь сыграть ещё?", reply_markup=kb)

# =============== КНОПКА НАЗАД ===============
@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📥 Crack Free", callback_data="download"),
        types.InlineKeyboardButton("🎯 Подробнее", callback_data="more"),
        types.InlineKeyboardButton("👥 Поделиться", callback_data="share"),
        types.InlineKeyboardButton("📢 Репорт", callback_data="report"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="stats"),
        types.InlineKeyboardButton("🌐 Crack Plus", callback_data="crack_plus"),
        types.InlineKeyboardButton("🎰 Колесо фортуны", callback_data="fortune_wheel"),
        types.InlineKeyboardButton("❌ Крестики-нолики", callback_data="tic_tac_toe"),
        types.InlineKeyboardButton("🏆 Купить статус", callback_data="buy_status"),
        types.InlineKeyboardButton("🛍 Crack Market", callback_data="market")
    )
    status, _ = get_status_and_bonus(uid)
    if status == "👑 Герцог":
        kb.add(types.InlineKeyboardButton("🎨 Кастомизация", callback_data="customize"))
    bot.send_message(uid, "Crack Sbornik - 💥 лучший сборник кряков именно для тебя!", reply_markup=kb)

# =============== КОМАНДЫ ===============
@bot.message_handler(commands=['start'])
def start(m):
    track_user(m)
    uid = m.from_user.id
    if is_banned(uid):
        bot.send_message(uid, "❌ Вы забанены!")
        return
    users.add(uid)
    add_coins_with_bonus(uid, 10, "start")
    bot.send_message(uid, f"💰 +10 монет с бонусом! Баланс: {get_coins(uid)}")
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📥 Crack Free", callback_data="download"),
        types.InlineKeyboardButton("🎯 Подробнее", callback_data="more"),
        types.InlineKeyboardButton("👥 Поделиться", callback_data="share"),
        types.InlineKeyboardButton("📢 Репорт", callback_data="report"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="stats"),
        types.InlineKeyboardButton("🌐 Crack Plus", callback_data="crack_plus"),
        types.InlineKeyboardButton("🎰 Колесо фортуны", callback_data="fortune_wheel"),
        types.InlineKeyboardButton("❌ Крестики-нолики", callback_data="tic_tac_toe"),
        types.InlineKeyboardButton("🏆 Купить статус", callback_data="buy_status"),
        types.InlineKeyboardButton("🛍 Crack Market", callback_data="market")
    )
    status, _ = get_status_and_bonus(uid)
    if status == "👑 Герцог":
        kb.add(types.InlineKeyboardButton("🎨 Кастомизация", callback_data="customize"))
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
        bot.send_message(uid, f"🎉 CRACK PLUS КУПЛЕН!\n🔗 {CRACK_PLUS_LINK}\n🔑 Ключ: {key}\n💰 Остаток: {get_coins(uid)}")
    else:
        bot.send_message(uid, f"❌ Не хватает монет! {coins} из {CRACK_PLUS_PRICE}")

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
        types.InlineKeyboardButton("💰 Выдать монеты", callback_data="admin_give_coins"),
        types.InlineKeyboardButton("💰 Забрать монеты", callback_data="admin_take_coins"),
        types.InlineKeyboardButton("📊 Логи действий", callback_data="admin_stats_log"),
        types.InlineKeyboardButton("🏆 Выдать статус", callback_data="admin_give_status")
    )
    bot.send_message(m.chat.id, "🔧 Админ-панель", reply_markup=kb)

@bot.message_handler(commands=['cancel'])
def cancel(m):
    track_user(m)
    uid = m.from_user.id
    if uid in waiting_for_report:
        del waiting_for_report[uid]
        bot.reply_to(m, "❌ Отменено")

@bot.message_handler(commands=['salary'])
def salary_command(m):
    uid = m.from_user.id
    status, _ = get_status_and_bonus(uid)
    if status != "👑 Герцог":
        bot.send_message(uid, "❌ Только для 👑 Герцог!")
        return
    if uid not in duke_settings:
        duke_settings[uid] = {}
    if duke_settings[uid].get("salary_taken") == time.strftime("%Y-%m-%d"):
        bot.send_message(uid, "❌ Сегодня уже получал! Завтра приходи.")
        return
    add_coins(uid, 100000)
    duke_settings[uid]["salary_taken"] = time.strftime("%Y-%m-%d")
    save_duke_settings()
    bot.send_message(uid, f"💰 Зарплата 100000 монет!\n💰 Баланс: {get_coins(uid)}")

# =============== СТАТИСТИКА ПОЛЬЗОВАТЕЛЯ ===============
@bot.callback_query_handler(func=lambda call: call.data == "stats")
def stats_callback(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if is_banned(uid):
        bot.send_message(uid, "❌ Вы забанены!")
        return
    coins = get_coins(uid)
    status, bonus = get_status_and_bonus(uid)
    bonus_percent = int((bonus - 1) * 100)
    stats = user_stats.get(uid, {})
    title = stats.get("title", "")
    text = f"📊 **Твоя статистика**\n\n"
    text += f"👤 {call.from_user.first_name}\n"
    if call.from_user.username:
        text += f"📱 @{call.from_user.username}\n"
    text += f"🆔 `{uid}`\n\n"
    text += f"💰 {coins} монет\n"
    text += f"🏆 {status}\n"
    if title:
        text += f"🏷 {title}\n"
    text += f"✨ +{bonus_percent}%\n"
    text += f"📈 {stats.get('total_earned',0)} всего\n"
    text += f"🎰 Фортуна: {stats.get('fortune_win',0)}\n"
    text += f"❌⭕ Крестики: {stats.get('ttt_win',0)}"
    bot.send_message(uid, text, parse_mode="Markdown")

# =============== КАСТОМИЗАЦИЯ ===============
@bot.callback_query_handler(func=lambda call: call.data == "customize")
def customize_menu(call):
    uid = call.from_user.id
    status, _ = get_status_and_bonus(uid)
    if status != "👑 Герцог":
        bot.answer_callback_query(call.id, "❌ Только для 👑 Герцог!", True)
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🌈 Радужный", callback_data="custom_rainbow"),
        types.InlineKeyboardButton("🔴 Красный", callback_data="custom_red"),
        types.InlineKeyboardButton("🔵 Синий", callback_data="custom_blue"),
        types.InlineKeyboardButton("🟢 Зелёный", callback_data="custom_green"),
        types.InlineKeyboardButton("🟣 Фиолетовый", callback_data="custom_purple"),
        types.InlineKeyboardButton("⚪ Белый", callback_data="custom_white"),
        types.InlineKeyboardButton("🌙 Тёмная тема", callback_data="custom_dark"),
        types.InlineKeyboardButton("☀️ Светлая тема", callback_data="custom_light"),
        types.InlineKeyboardButton("🎨 Кастомный фон", callback_data="custom_bg"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")
    )
    bot.answer_callback_query(call.id)
    bot.send_message(uid, "🎨 **Кастомизация**", parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("custom_"))
def apply_custom(call):
    uid = call.from_user.id
    if uid not in duke_settings:
        duke_settings[uid] = {}
    duke_settings[uid]["color"] = call.data.replace("custom_", "")
    save_duke_settings()
    bot.answer_callback_query(call.id, "✅ Сохранено!", True)

# =============== МАГАЗИН CRACK MARKET ===============
@bot.callback_query_handler(func=lambda call: call.data == "market")
def market_menu(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    coins = get_coins(uid)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🏆 Привилегии", callback_data="market_privileges"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")
    )
    bot.answer_callback_query(call.id)
    bot.send_message(uid, f"🛍 **Crack Market**\n💰 Баланс: {coins}", parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("market_"))
def market_category(call):
    uid = call.from_user.id
    category = call.data.replace("market_", "")
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    coins = get_coins(uid)
    status, _ = get_status_and_bonus(uid)
    discount = 0.25 if status == "👑 Герцог" else 0
    kb = types.InlineKeyboardMarkup(row_width=1)
    text = f"🛍 **{category.upper()}**\n💰 Баланс: {coins}\n"
    if discount > 0:
        text += f"🎉 Скидка {int(discount*100)}%\n"
    for item_name, item_data in MARKET_ITEMS.items():
        if item_data["type"] == "status":
            price = item_data["price"]
            final_price = int(price * (1 - discount))
            kb.add(types.InlineKeyboardButton(f"{item_name.split('_')[1]} — {final_price}", callback_data=f"buy_{item_name}"))
            text += f"• {item_name.split('_')[1]}: {final_price}"
            if item_data.get("bonus"):
                text += f" (+{int((item_data['bonus']-1)*100)}%)"
            if item_data.get("no_cd"):
                text += " (без КД)"
            text += "\n"
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="market"))
    bot.answer_callback_query(call.id)
    bot.send_message(uid, text, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_item(call):
    uid = call.from_user.id
    item_key = call.data.replace("buy_", "")
    if item_key not in MARKET_ITEMS:
        bot.answer_callback_query(call.id, "❌ Товар не найден!", True)
        return
    item = MARKET_ITEMS[item_key]
    price = item["price"]
    status, _ = get_status_and_bonus(uid)
    discount = 0.25 if status == "👑 Герцог" else 0
    final_price = int(price * (1 - discount))
    coins = get_coins(uid)
    if coins < final_price:
        bot.answer_callback_query(call.id, f"❌ Нужно {final_price}, у тебя {coins}", True)
        return
    remove_coins(uid, final_price)
    if item["type"] == "status":
        status_name = item_key.split('_')[1]
        if uid not in user_stats:
            user_stats[uid] = {"admin_give":0,"admin_take":0,"fortune_win":0,"ttt_win":0,"download":0,"report":0,"total_earned":0,"status":"","title":""}
        user_stats[uid]["status"] = status_name
        save_stats()
        bot.answer_callback_query(call.id, f"✅ Статус {status_name} куплен!", True)
        bot.send_message(uid, f"🎉 Статус {status_name} куплен!\n💰 Остаток: {get_coins(uid)}")
    admin_share = int(final_price * 0.3)
    add_coins(ADMIN_ID, admin_share)
    bot.send_message(ADMIN_ID, f"💰 Админ получил {admin_share} от {item_key} от {uid}")

# =============== МАГАЗИН СТАТУСОВ ===============
@bot.callback_query_handler(func=lambda call: call.data == "buy_status")
def buy_status_menu(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    coins = get_coins(uid)
    current_status, bonus = get_status_and_bonus(uid)
    status, _ = get_status_and_bonus(uid)
    discount = 0.25 if status == "👑 Герцог" else 0
    kb = types.InlineKeyboardMarkup(row_width=1)
    for status_name, info in STATUS_INFO.items():
        if status_name != "🟢 Новичок":
            price = info["price"]
            final_price = int(price * (1 - discount))
            kb.add(types.InlineKeyboardButton(f"{status_name} — {final_price}", callback_data=f"buy_status_{status_name}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu"))
    text = f"🏆 **Магазин статусов**\n💰 {coins}\n📊 Твой статус: {current_status}\n✨ Бонус: +{int((bonus-1)*100)}%\n"
    if discount > 0:
        text += f"🎉 Скидка {int(discount*100)}%\n"
    bot.answer_callback_query(call.id)
    bot.send_message(uid, text, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_status_"))
def show_status_info(call):
    uid = call.from_user.id
    status_name = call.data.replace("buy_status_", "")
    info = STATUS_INFO.get(status_name, {})
    price = info.get("price", 0)
    bonus = info.get("bonus", 1.0)
    status, _ = get_status_and_bonus(uid)
    discount = 0.25 if status == "👑 Герцог" else 0
    final_price = int(price * (1 - discount))
    text = f"🏆 **{status_name}**\n💰 {final_price}"
    if discount > 0:
        text += f" (было {price})"
    text += f"\n✨ +{int((bonus-1)*100)}%\n⚠️ Навсегда"
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Купить", callback_data=f"confirm_buy_{status_name}"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="buy_status")
    )
    bot.answer_callback_query(call.id)
    bot.send_message(uid, text, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_buy_"))
def confirm_buy_status(call):
    uid = call.from_user.id
    status_name = call.data.replace("confirm_buy_", "")
    info = STATUS_INFO.get(status_name, {})
    price = info.get("price", 0)
    status, _ = get_status_and_bonus(uid)
    discount = 0.25 if status == "👑 Герцог" else 0
    final_price = int(price * (1 - discount))
    coins = get_coins(uid)
    current_status, _ = get_status_and_bonus(uid)
    status_order = ["🟢 Новичок", "🔵 Продвинутый", "🟣 Опытный", "🟠 Эксперт", "🔴 Мастер", "👑 Бог", "👑 Герцог"]
    current_idx = status_order.index(current_status) if current_status in status_order else 0
    new_idx = status_order.index(status_name) if status_name in status_order else 0
    if new_idx <= current_idx:
        bot.answer_callback_query(call.id, f"❌ У тебя уже {current_status}!", True)
        return
    if coins < final_price:
        bot.answer_callback_query(call.id, f"❌ Нужно {final_price}, у тебя {coins}", True)
        return
    remove_coins(uid, final_price)
    admin_share = int(final_price * 0.5)
    add_coins(ADMIN_ID, admin_share)
    bot.send_message(ADMIN_ID, f"💰 Админ получил {admin_share} от {status_name} от {uid}")
    if uid not in user_stats:
        user_stats[uid] = {"admin_give":0,"admin_take":0,"fortune_win":0,"ttt_win":0,"download":0,"report":0,"total_earned":0,"status":"","title":""}
    user_stats[uid]["status"] = status_name
    save_stats()
    bot.answer_callback_query(call.id, f"✅ Статус {status_name} куплен!", True)
    bot.send_message(uid, f"🎉 Статус {status_name} куплен!\n✨ Бонус +{int((info['bonus']-1)*100)}%\n💰 Остаток: {get_coins(uid)}")

# =============== АДМИН-ФУНКЦИИ ===============
@bot.callback_query_handler(func=lambda call: call.data == "admin_give_coins")
def give_coins_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💰 Введите ID и сумму:")
    bot.register_next_step_handler(msg, process_give_coins)

def process_give_coins(m):
    if not is_admin(m.from_user.id):
        return
    try:
        uid, amt = map(int, m.text.split())
        if amt < 1 or amt > 100000:
            bot.send_message(m.chat.id, "❌ 1-100000")
            return
        add_coins_with_bonus(uid, amt, "admin_give")
        bot.send_message(m.chat.id, f"✅ Выдано {amt}\n💰 Баланс: {get_coins(uid)}")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка! Пример: 123456789 500")

@bot.callback_query_handler(func=lambda call: call.data == "admin_take_coins")
def take_coins_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💰 Введите ID и сумму для списания:")
    bot.register_next_step_handler(msg, process_take_coins)

def process_take_coins(m):
    if not is_admin(m.from_user.id):
        return
    try:
        uid, amt = map(int, m.text.split())
        if amt < 1:
            bot.send_message(m.chat.id, "❌ >0")
            return
        if get_coins(uid) < amt:
            bot.send_message(m.chat.id, f"❌ У {uid} недостаточно!")
            return
        remove_coins(uid, amt)
        update_user_stat(uid, "admin_take", amt)
        bot.send_message(m.chat.id, f"✅ Списано {amt}\n💰 Баланс: {get_coins(uid)}")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка! Пример: 123456789 500")

@bot.callback_query_handler(func=lambda call: call.data == "admin_ban")
def ban_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "🚫 Введите ID:")
    bot.register_next_step_handler(msg, ban_user)

def ban_user(m):
    try:
        uid = int(m.text.strip())
        if uid == ADMIN_ID:
            bot.send_message(m.chat.id, "❌ Нельзя забанить админа!")
            return
        blacklist.add(uid)
        save_blacklist()
        bot.send_message(m.chat.id, f"✅ {uid} забанен")
        try:
            bot.send_message(uid, "❌ Вы забанены!")
        except:
            pass
    except:
        bot.send_message(m.chat.id, "❌ Ошибка!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_unban")
def unban_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "✅ Введите ID:")
    bot.register_next_step_handler(msg, unban_user)

def unban_user(m):
    try:
        uid = int(m.text.strip())
        if uid in blacklist:
            blacklist.remove(uid)
            save_blacklist()
            bot.send_message(m.chat.id, f"✅ {uid} разбанен")
            try:
                bot.send_message(uid, "✅ Вы разбанены!")
            except:
                pass
        else:
            bot.send_message(m.chat.id, f"❌ {uid} не в ЧС")
    except:
        bot.send_message(m.chat.id, "❌ Ошибка!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_banlist")
def banlist(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    if blacklist:
        bot.send_message(call.message.chat.id, f"📋 Забаненные:\n" + "\n".join(str(x) for x in blacklist))
    else:
        bot.send_message(call.message.chat.id, "📋 Пусто")

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    total_coins = sum(coins_data.values())
    bot.send_message(call.message.chat.id, f"📊 **Статистика**\n📥 Скачиваний: {download_count}\n👥 Пользователей: {len(users)}\n💰 Всего монет: {total_coins}\n🎰 Фортуна: {sum(s.get('fortune_win',0) for s in user_stats.values())}\n❌⭕ Крестики: {sum(s.get('ttt_win',0) for s in user_stats.values())}\n📋 В ЧС: {len(blacklist)}", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_users")
def admin_users(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"👥 Пользователей: {len(users)}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_tracker")
def admin_tracker(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    if not message_tracker:
        bot.send_message(call.message.chat.id, "📊 Нет данных")
        return
    top = sorted(message_tracker.items(), key=lambda x: x[1]["count"], reverse=True)[:20]
    text = "📊 Топ по сообщениям:\n"
    for i, (uid, d) in enumerate(top, 1):
        name = d.get('username') or d.get('name', str(uid))[:15]
        text += f"{i}. {name} — {d['count']}\n"
    bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats_log")
def admin_stats_log(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    if not user_stats:
        bot.send_message(call.message.chat.id, "📊 Нет данных")
        return
    sorted_users = sorted(user_stats.items(), key=lambda x: get_coins(x[0]), reverse=True)[:20]
    text = "📊 Логи действий:\n\n"
    for uid, data in sorted_users:
        status, bonus = get_status_and_bonus(uid)
        text += f"👤 ID: {uid}\n"
        text += f"   🏆 {status} (+{int((bonus-1)*100)}%)\n"
        text += f"   ✅ Выдано: {data['admin_give']}\n"
        text += f"   ❌ Забрано: {data['admin_take']}\n"
        text += f"   🎰 Фортуна: {data['fortune_win']}\n"
        text += f"   ❌⭕ Крестики: {data['ttt_win']}\n"
        text += f"   💰 Баланс: {get_coins(uid)}\n\n"
    bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == "admin_give_status")
def admin_give_status_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    for status in ["🟢 Новичок", "🔵 Продвинутый", "🟣 Опытный", "🟠 Эксперт", "🔴 Мастер", "👑 Бог", "👑 Герцог"]:
        kb.add(types.InlineKeyboardButton(status, callback_data=f"admin_give_status_{status}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "🏆 Выбери статус:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_give_status_"))
def admin_give_status_ask(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    status_name = call.data.replace("admin_give_status_", "")
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"✏️ Введите ID пользователя для выдачи {status_name}:")
    bot.register_next_step_handler(msg, lambda m: admin_give_status(m, status_name))

def admin_give_status(m, status_name):
    if not is_admin(m.from_user.id):
        return
    try:
        uid = int(m.text.strip())
        if uid not in user_stats:
            user_stats[uid] = {"admin_give":0,"admin_take":0,"fortune_win":0,"ttt_win":0,"download":0,"report":0,"total_earned":0,"status":"","title":""}
        user_stats[uid]["status"] = status_name
        save_stats()
        bot.send_message(m.chat.id, f"✅ {uid} выдан статус {status_name}")
        try:
            bot.send_message(uid, f"🏆 Админ выдал тебе статус {status_name}!")
        except:
            pass
    except:
        bot.send_message(m.chat.id, "❌ Ошибка! Введите ID")

@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def admin_back(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    admin(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
def broadcast_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "📢 Введите текст для рассылки:")
    bot.register_next_step_handler(msg, broadcast)

def broadcast(m):
    text = m.text.strip()
    success = fail = 0
    bot.send_message(m.chat.id, "📢 Начинаю рассылку...")
    for uid in users:
        if is_banned(uid):
            continue
        try:
            bot.send_message(uid, f"📢 {text}")
            success += 1
        except:
            fail += 1
        time.sleep(0.05)
    bot.send_message(m.chat.id, f"✅ Рассылка: {success} доставлено, {fail} ошибок")

@bot.callback_query_handler(func=lambda call: call.data == "admin_change_link")
def change_link_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "📝 Отправьте новую ссылку:")
    bot.register_next_step_handler(msg, change_link)

def change_link(m):
    global SOFT_LINK
    SOFT_LINK = m.text.strip()
    bot.send_message(m.chat.id, f"✅ Ссылка изменена!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_change_image")
def change_image_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "🖼 Отправьте новую ссылку на картинку:")
    bot.register_next_step_handler(msg, change_image)

def change_image(m):
    global IMAGE_URL
    IMAGE_URL = m.text.strip()
    bot.send_message(m.chat.id, f"✅ Картинка изменена!")

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
    add_coins_with_bonus(uid, 50, "report")
    bot.send_message(uid, "✅ Жалоба отправлена! +50 монет с бонусом")
    admin_message = f"📢 НОВАЯ ЖАЛОБА!\n👤 {user_name}\n🆔 {uid}\n📱 {user_username}\n📝 {report_text}\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{uid}"))
    bot.send_message(ADMIN_ID, admin_message, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def reply_to_user(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    uid = int(call.data.split('_')[1])
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"✏️ Введите ответ для {uid}:")
    bot.register_next_step_handler(msg, lambda m: send_reply(m, uid))

def send_reply(m, uid):
    try:
        bot.send_message(uid, f"📢 Ответ администратора:\n\n{m.text.strip()}")
        bot.send_message(m.chat.id, f"✅ Ответ отправлен")
    except:
        bot.send_message(m.chat.id, f"❌ Ошибка")

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
    load_stats()
    load_boosts()
    load_permanent()
    load_duke_settings()
    print("✅ Бот запущен!")
    try:
        bot.send_message(ADMIN_ID, "✅ Бот запущен!")
    except:
        print("⚠️ Админ не начал диалог с ботом!")
    bot.remove_webhook()
    time.sleep(1)
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'bot-tg-1-x4tg.onrender.com')}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
