import os
import time
import random
import string
import threading
from flask import Flask, request
import telebot
from telebot import types

# =============== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) ===============
TOKEN = "8294974465:AAFfeR0krjHmDUwdQm7rO5N6VfnV8ZvFrOI"  # ⚠️ ЗАМЕНИ НА НОВЫЙ ТОКЕН!
ADMIN_ID = 7859226148  # ⚠️ ЗАМЕНИ НА СВОЙ ID

SOFT_LINK = "https://www.mediafire.com/file/giyvpt6yuy9so7m/Crack_Sbornik.exe/file"
IMAGE_URL = "https://i.ibb.co/YBXZt30f/ggdoksraz.png"
CRACK_PLUS_LINK = "https://www.mediafire.com/file/2w6a3y18ke8vr94/Crack_Plus.exe/file"
CRACK_PLUS_PRICE = 60000

# =============== СТАТУСЫ И ИХ БОНУСЫ ===============
STATUS_INFO = {
    "🟢 Новичок": {"price": 0, "bonus": 1.0},
    "🔵 Продвинутый": {"price": 1000, "bonus": 1.1},
    "🟣 Опытный": {"price": 5000, "bonus": 1.2},
    "🟠 Эксперт": {"price": 20000, "bonus": 1.3},
    "🔴 Мастер": {"price": 50000, "bonus": 1.4},
    "👑 Бог": {"price": 100000, "bonus": 1.5}
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

BLACKLIST_FILE = "blacklist.txt"
MESSAGE_FILE = "messages.txt"
COINS_FILE = "coins.txt"
STATS_FILE = "user_stats.txt"

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
                            "status": parts[10] if len(parts) > 10 else ""
                        }
    print(f"✅ Загружена статистика: {len(user_stats)} пользователей")

def save_stats():
    with open(STATS_FILE, 'w') as f:
        for uid, data in user_stats.items():
            f.write(f"{uid}|{uid}|{uid}|{data['admin_give']}|{data['admin_take']}|{data['fortune_win']}|{data['ttt_win']}|{data['download']}|{data['report']}|{data['total_earned']}|{data.get('status', '')}\n")

def update_user_stat(uid, stat_name, amount):
    if uid not in user_stats:
        user_stats[uid] = {
            "admin_give": 0, "admin_take": 0, "fortune_win": 0, "ttt_win": 0,
            "download": 0, "report": 0, "total_earned": 0, "status": ""
        }
    if stat_name in user_stats[uid]:
        user_stats[uid][stat_name] += amount
    save_stats()

def update_total_earned(uid, amount):
    if uid not in user_stats:
        user_stats[uid] = {
            "admin_give": 0, "admin_take": 0, "fortune_win": 0, "ttt_win": 0,
            "download": 0, "report": 0, "total_earned": 0, "status": ""
        }
    user_stats[uid]["total_earned"] += amount
    save_stats()

def get_total_earned(uid):
    if uid in user_stats:
        return user_stats[uid].get("total_earned", 0)
    return 0

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

# =============== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===============
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

def bot_move(board):
    if random.choice([True, False]):
        for i in range(9):
            if board[i] == "":
                board[i] = "O"
                if check_winner(board) == "O":
                    return i
                board[i] = ""
        for i in range(9):
            if board[i] == "":
                board[i] = "X"
                if check_winner(board) == "X":
                    board[i] = ""
                    return i
                board[i] = ""
        if board[4] == "":
            return 4
        corners = [0, 2, 6, 8]
        random.shuffle(corners)
        for i in corners:
            if board[i] == "":
                return i
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
        bot.answer_callback_query(call.id, f"🎉 Поздравляем! Ты выиграл {final_amount} монет (x2 от {bet} + бонус статуса)!", show_alert=True)
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
        move = bot_move(board)
        if move is not None:
            board[move] = "O"
        winner = check_winner(board)
        if winner == "O":
            bot.edit_message_text(game_over_message("O", board, bet), chat_id, message_id, parse_mode="Markdown")
            del ttt_games[uid]
            bot.answer_callback_query(call.id, f"😔 Бот выиграл! Ты проиграл {bet} монет", show_alert=True)
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
        types.InlineKeyboardButton("🎲 10 монет", callback_data="fortune_10"),
        types.InlineKeyboardButton("🎲 50 монет", callback_data="fortune_50"),
        types.InlineKeyboardButton("🎲 100 монет", callback_data="fortune_100"),
        types.InlineKeyboardButton("🎲 300 монет", callback_data="fortune_300"),
        types.InlineKeyboardButton("🎲 5000 монет", callback_data="fortune_5000"),
        types.InlineKeyboardButton("🎲 10000 монет", callback_data="fortune_10000"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")
    )
    bot.answer_callback_query(call.id)
    bot.send_message(uid, f"🎰 **Колесо фортуны**\n\n💰 Твой баланс: {coins} монет\n\nВыбери ставку (50% победа):", parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("fortune_"))
def fortune_spin(call):
    uid = call.from_user.id
    bet = int(call.data.split('_')[1])
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    coins = get_coins(uid)
    if coins < bet:
        bot.answer_callback_query(call.id, f"❌ Не хватает монет! Нужно {bet}, у тебя {coins}", True)
        return
    bot.answer_callback_query(call.id, "🎰 Колесо крутится...", show_alert=False)
    is_win = random.choice([True, False])
    if is_win:
        if bet == 10:
            prizes = [10, 20, 50, 100]
            win = random.choice(prizes)
        elif bet == 50:
            prizes = [50, 100, 150, 250]
            win = random.choice(prizes)
        elif bet == 100:
            prizes = [100, 200, 300, 500]
            win = random.choice(prizes)
        elif bet == 300:
            prizes = [300, 600, 900, 1500]
            win = random.choice(prizes)
        elif bet == 5000:
            prizes = [5000, 10000, 15000, 20000]
            win = random.choice(prizes)
        elif bet == 10000:
            prizes = [10000, 20000, 30000, 40000]
            win = random.choice(prizes)
        else:
            prizes = [10, 20, 50, 100]
            win = random.choice(prizes)
        remove_coins(uid, bet)
        add_coins_with_bonus(uid, win, "fortune_win")
        final_coins = get_coins(uid)
        result_text = f"🎉 **ПОБЕДА!** 🎉\n\n💰 Ставка: {bet} монет\n🏆 Выигрыш: {win} монет\n💵 Чистый выигрыш: +{win - bet} монет\n💰 Новый баланс: {final_coins} монет"
        bot.send_message(uid, result_text, parse_mode="Markdown")
    else:
        remove_coins(uid, bet)
        final_coins = get_coins(uid)
        result_text = f"😔 **ПРОИГРЫШ!** 😔\n\n💰 Ставка: {bet} монет\n💵 Потеряно: -{bet} монет\n💰 Новый баланс: {final_coins} монет"
        bot.send_message(uid, result_text, parse_mode="Markdown")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🎰 Сыграть ещё", callback_data="fortune_wheel"))
    kb.add(types.InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu"))
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
        types.InlineKeyboardButton("🏆 Купить статус", callback_data="buy_status")
    )
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
    bot.send_message(uid, f"💰 +10 монет с учётом бонуса статуса! Баланс: {get_coins(uid)}")
    
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
        types.InlineKeyboardButton("🏆 Купить статус", callback_data="buy_status")
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
        bot.send_message(uid, f"🎉 CRACK PLUS КУПЛЕН!\n\n🔗 Ссылка:\n{CRACK_PLUS_LINK}\n\n🔑 Ключ: {key}\n💰 Остаток: {get_coins(uid)}")
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

# =============== МАГАЗИН СТАТУСОВ ===============
@bot.callback_query_handler(func=lambda call: call.data == "buy_status")
def buy_status_menu(call):
    uid = call.from_user.id
    if is_banned(uid):
        bot.answer_callback_query(call.id, "❌ Вы забанены!", True)
        return
    
    coins = get_coins(uid)
    current_status, bonus = get_status_and_bonus(uid)
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    for status_name, info in STATUS_INFO.items():
        if status_name != "🟢 Новичок":
            price = info["price"]
            kb.add(types.InlineKeyboardButton(f"{status_name} — {price} монет", callback_data=f"buy_status_{status_name}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu"))
    
    text = f"🏆 **Магазин статусов**\n\n"
    text += f"💰 Твой баланс: {coins} монет\n"
    text += f"📊 Твой статус: {current_status}\n"
    text += f"✨ **Твой бонус к заработку:** +{int((bonus - 1) * 100)}%\n\n"
    text += "**Доступные статусы:**"
    
    bot.answer_callback_query(call.id)
    bot.send_message(uid, text, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_status_"))
def show_status_info(call):
    uid = call.from_user.id
    status_name = call.data.replace("buy_status_", "")
    
    info = STATUS_INFO.get(status_name, {})
    price = info.get("price", 0)
    bonus = info.get("bonus", 1.0)
    bonus_percent = int((bonus - 1) * 100)
    
    text = f"🏆 **{status_name}**\n\n"
    text += f"💰 Цена: {price} монет\n"
    text += f"✨ Бонус к заработку: +{bonus_percent}%\n\n"
    text += f"⚠️ Статус действует **навсегда** после покупки!"
    
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
    
    coins = get_coins(uid)
    current_status, _ = get_status_and_bonus(uid)
    
    status_order = ["🟢 Новичок", "🔵 Продвинутый", "🟣 Опытный", "🟠 Эксперт", "🔴 Мастер", "👑 Бог"]
    current_index = status_order.index(current_status) if current_status in status_order else 0
    new_index = status_order.index(status_name) if status_name in status_order else 0
    
    if new_index <= current_index:
        bot.answer_callback_query(call.id, f"❌ У тебя уже есть статус {current_status} или выше!", True)
        return
    
    if coins < price:
        bot.answer_callback_query(call.id, f"❌ Не хватает монет! Нужно {price}, у тебя {coins}", True)
        return
    
    remove_coins(uid, price)
    
    if uid not in user_stats:
        user_stats[uid] = {
            "admin_give": 0, "admin_take": 0, "fortune_win": 0, "ttt_win": 0,
            "download": 0, "report": 0, "total_earned": 0, "status": ""
        }
    
    user_stats[uid]["status"] = status_name
    save_stats()
    
    bot.answer_callback_query(call.id, f"✅ Ты купил статус {status_name}!", True)
    
    text = f"🎉 **Поздравляем!** 🎉\n\n"
    text += f"Ты приобрёл статус **{status_name}** за {price} монет!\n\n"
    text += f"✨ **Твой новый бонус к заработку:** +{int((info['bonus'] - 1) * 100)}%\n\n"
    text += f"💰 Твой текущий баланс: {get_coins(uid)} монет"
    
    bot.send_message(uid, text, parse_mode="Markdown")

# =============== ВЫДАЧА СТАТУСА АДМИНОМ ===============
@bot.callback_query_handler(func=lambda call: call.data == "admin_give_status")
def give_status_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    status_order = ["🟢 Новичок", "🔵 Продвинутый", "🟣 Опытный", "🟠 Эксперт", "🔴 Мастер", "👑 Бог"]
    for status in status_order:
        kb.add(types.InlineKeyboardButton(status, callback_data=f"admin_status_{status}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back_to_panel"))
    
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "🏆 **Выбери статус для выдачи:**", parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_status_"))
def ask_user_id_for_status(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    
    status_name = call.data.replace("admin_status_", "")
    bot.answer_callback_query(call.id)
    
    msg = bot.send_message(call.message.chat.id, f"✏️ Введите ID пользователя, которому выдать статус **{status_name}**:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, lambda m: give_status_to_user(m, status_name))

def give_status_to_user(message, status_name):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Нет доступа!")
        return
    
    try:
        uid = int(message.text.strip())
    except:
        bot.send_message(message.chat.id, "❌ Ошибка! Введите ID пользователя (число).")
        return
    
    if uid not in user_stats:
        user_stats[uid] = {
            "admin_give": 0, "admin_take": 0, "fortune_win": 0, "ttt_win": 0,
            "download": 0, "report": 0, "total_earned": 0, "status": ""
        }
    
    user_stats[uid]["status"] = status_name
    save_stats()
    
    bot.send_message(message.chat.id, f"✅ Пользователю `{uid}` выдан статус **{status_name}**!", parse_mode="Markdown")
    
    try:
        bot.send_message(uid, f"🏆 Администратор выдал тебе статус **{status_name}**!\n\nПоздравляем! 🎉", parse_mode="Markdown")
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "admin_back_to_panel")
def admin_back_to_panel(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    admin(call.message)

# =============== ПОКАЗ ЛОГОВ ДЕЙСТВИЙ ===============
@bot.callback_query_handler(func=lambda call: call.data == "admin_stats_log")
def show_user_stats(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    if not user_stats:
        bot.send_message(call.message.chat.id, "📊 Нет данных.")
        return
    sorted_users = sorted(user_stats.items(), key=lambda x: get_coins(x[0]), reverse=True)
    text = "📊 *Логи действий:*\n\n"
    for uid, data in sorted_users[:30]:
        balance = get_coins(uid)
        status, bonus = get_status_and_bonus(uid)
        bonus_percent = int((bonus - 1) * 100)
        text += f"👤 *ID: {uid}*\n"
        text += f"   🏆 Статус: {status} (+{bonus_percent}%)\n"
        text += f"   ✅ Выдано: {data['admin_give']}\n"
        text += f"   ❌ Забрано: {data['admin_take']}\n"
        text += f"   🎰 Фортуна: {data['fortune_win']}\n"
        text += f"   ❌⭕ Крестики: {data['ttt_win']}\n"
        text += f"   💰 Баланс: {balance}\n\n"
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

# =============== ОБРАБОТЧИК CRACK PLUS ===============
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
    bot.send_message(uid, "🌐 **Crack Plus**\n\n💲 цена 60000 монет\n\nНапишите /buy чтобы купить!\n\n/start дает монеты с бонусом статуса!", parse_mode="Markdown")

# =============== ВЫДАЧА/ЗАБОР МОНЕТ ===============
@bot.callback_query_handler(func=lambda call: call.data == "admin_give_coins")
def give_coins_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💰 Введите ID и сумму:\nПример: `123456789 500`", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_give_coins)

def process_give_coins(message):
    try:
        uid, amt = map(int, message.text.split())
        if amt < 1 or amt > 100000:
            bot.send_message(message.chat.id, "❌ Сумма от 1 до 100000!")
            return
        add_coins_with_bonus(uid, amt, "admin_give")
        bot.send_message(message.chat.id, f"✅ Выдано {amt} монет с бонусом!\n💰 Баланс: {get_coins(uid)}")
        try:
            bot.send_message(uid, f"💰 Вам начислено {amt} монет с бонусом статуса!")
        except:
            pass
    except:
        bot.send_message(message.chat.id, "❌ Ошибка! Пример: 123456789 500")

@bot.callback_query_handler(func=lambda call: call.data == "admin_take_coins")
def take_coins_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💰 Введите ID и сумму для списания:\nПример: `123456789 500`", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_take_coins)

def process_take_coins(message):
    try:
        uid, amt = map(int, message.text.split())
        if amt < 1:
            bot.send_message(message.chat.id, "❌ Сумма > 0!")
            return
        if get_coins(uid) < amt:
            bot.send_message(message.chat.id, f"❌ У пользователя {uid} недостаточно монет!")
            return
        remove_coins(uid, amt)
        update_user_stat(uid, "admin_take", amt)
        bot.send_message(message.chat.id, f"✅ Списано {amt} монет\n💰 Баланс: {get_coins(uid)}")
        try:
            bot.send_message(uid, f"💰 У вас списано {amt} монет администратором!")
        except:
            pass
    except:
        bot.send_message(message.chat.id, "❌ Ошибка! Пример: 123456789 500")

# =============== ОБРАБОТЧИК КНОПОК (ОСНОВНОЙ) ===============
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
        bot.answer_callback_query(call.id, "✏️ Введите ответ")
        msg = bot.send_message(call.message.chat.id, f"Введите ответ для {user_id}:")
        bot.register_next_step_handler(msg, lambda m: send_reply(m, user_id))
        return
    
    # СТАТИСТИКА
    if call.data == "stats":
        coins = get_coins(uid)
        status, bonus = get_status_and_bonus(uid)
        bonus_percent = int((bonus - 1) * 100)
        stats = user_stats.get(uid, {})
        fortune_win = stats.get("fortune_win", 0)
        ttt_win = stats.get("ttt_win", 0)
        admin_give = stats.get("admin_give", 0)
        total_earned = stats.get("total_earned", 0)
        
        text = f"📊 **Твоя статистика**\n\n"
        text += f"👤 **Имя:** {call.from_user.first_name}\n"
        if call.from_user.username:
            text += f"📱 **Username:** @{call.from_user.username}\n"
        text += f"🆔 **ID:** `{uid}`\n\n"
        text += f"💰 **Баланс:** {coins} монет\n"
        text += f"🏆 **Статус:** {status}\n"
        text += f"✨ **Бонус к заработку:** +{bonus_percent}%\n"
        text += f"📈 **Всего заработано:** {total_earned} монет\n\n"
        text += f"🎰 **Выигрыш в Фортуне:** {fortune_win} монет\n"
        text += f"❌⭕ **Выигрыш в Крестиках:** {ttt_win} монет\n"
        text += f"👑 **Получено от админа:** {admin_give} монет\n"
        
        bot.answer_callback_query(call.id)
        bot.send_message(uid, text, parse_mode="Markdown")
        return
    
    # Колесо фортуны
    if call.data == "fortune_wheel":
        fortune_wheel_menu(call)
        return
    
    if call.data.startswith("fortune_"):
        fortune_spin(call)
        return
    
    # Крестики-нолики
    if call.data == "tic_tac_toe":
        tic_tac_toe_menu(call)
        return
    
    if call.data.startswith("ttt_bet_"):
        start_ttt_game(call)
        return
    
    if call.data.startswith("ttt_") and not call.data.startswith("ttt_bet_"):
        ttt_move(call)
        return
    
    # Магазин статусов
    if call.data == "buy_status":
        buy_status_menu(call)
        return
    
    if call.data.startswith("buy_status_"):
        show_status_info(call)
        return
    
    if call.data.startswith("confirm_buy_"):
        confirm_buy_status(call)
        return
    
    # Админ-выдача статуса
    if call.data == "admin_give_status":
        give_status_menu(call)
        return
    
    if call.data.startswith("admin_status_"):
        ask_user_id_for_status(call)
        return
    
    if call.data == "admin_back_to_panel":
        admin_back_to_panel(call)
        return
    
    # Логи действий
    if call.data == "admin_stats_log":
        show_user_stats(call)
        return
    
    # Назад
    if call.data == "back_to_menu":
        back_to_menu(call)
        return
    
    # КД для остальных кнопок
    cd = check_cd(uid)
    if cd > 0:
        bot.answer_callback_query(call.id, f"⏳ {cd} сек!", True)
        return
    update_cd(uid)
    
    # Обычные кнопки
    if call.data == "download":
        global download_count
        download_count += 1
        update_user_stat(uid, "download", 1)
        bot.answer_callback_query(call.id, "✅ Ссылка отправлена!")
        bot.send_message(uid, f"🔗 {SOFT_LINK}")
    elif call.data == "more":
        bot.answer_callback_query(call.id, "📸")
        bot.send_photo(uid, IMAGE_URL, caption="☢️ антивирус может ругаться")
    elif call.data == "share":
        bot.answer_callback_query(call.id)
        bot.send_message(uid, f"👥 Поделиться:\nhttps://t.me/{bot.get_me().username}")
    elif call.data == "report":
        waiting_for_report[uid] = True
        bot.answer_callback_query(call.id)
        bot.send_message(uid, "✍️ Напишите текст жалобы (/cancel для отмены)")
    elif call.data == "crack_plus":
        bot.answer_callback_query(call.id)
        bot.send_message(uid, "🌐 **Crack Plus**\n\n💲 цена 60000 монет\n\nНапишите /buy чтобы купить!", parse_mode="Markdown")
    elif is_admin(uid) and call.data.startswith('admin_'):
        if call.data == "admin_stats":
            bot.answer_callback_query(call.id)
            bot.send_message(uid, f"📊 Статистика:\n📥 Скачиваний: {download_count}\n👥 Пользователей: {len(users)}")
        elif call.data == "admin_users":
            bot.answer_callback_query(call.id)
            bot.send_message(uid, f"👥 Пользователей: {len(users)}")
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
                bot.send_message(uid, "📊 Нет данных")
                return
            top = sorted(message_tracker.items(), key=lambda x: x[1]["count"], reverse=True)[:20]
            text = "📊 Топ по сообщениям:\n"
            for i, (uid, d) in enumerate(top, 1):
                name = d.get('username') or d.get('name', str(uid))[:15]
                text += f"{i}. {name} — {d['count']}\n"
            bot.send_message(uid, text)

def send_reply(message, user_id):
    reply_text = message.text.strip()
    try:
        bot.send_message(user_id, f"📢 Ответ администратора:\n\n{reply_text}")
        bot.send_message(message.chat.id, f"✅ Ответ отправлен")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

def change_link(m):
    global SOFT_LINK
    SOFT_LINK = m.text.strip()
    bot.send_message(m.chat.id, f"✅ Ссылка изменена!")

def change_image(m):
    global IMAGE_URL
    IMAGE_URL = m.text.strip()
    bot.send_message(m.chat.id, f"✅ Картинка изменена!")

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
    add_coins_with_bonus(uid, 50, "report")
    bot.send_message(uid, "✅ Жалоба отправлена! +50 монет с бонусом")
    admin_message = f"📢 **НОВАЯ ЖАЛОБА!**\n\n👤 {user_name}\n🆔 ID: {uid}\n📱 {user_username}\n📝 {report_text}\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{uid}"))
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
    load_stats()
    print(f"✅ Загружено: {len(coins_data)} кошельков, {len(message_tracker)} в трекере, {len(blacklist)} в ЧС, {len(user_stats)} в статистике")
    print(f"✅ Бот запущен! Команды: /start, /buy, /admin, /test")
    try:
        bot.send_message(ADMIN_ID, "✅ Бот запущен!")
    except:
        print("⚠️ Админ не начал диалог с ботом! Напишите /start")
    bot.remove_webhook()
    time.sleep(1)
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'bot-tg-1-x4tg.onrender.com')}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook: {webhook_url}")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
