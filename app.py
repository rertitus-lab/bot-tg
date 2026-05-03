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

# Крестики-нолики
ttt_games = {}

# Логирование действий пользователей
user_stats = {}
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

# =============== ФУНКЦИИ ЛОГИРОВАНИЯ ===============
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
                            "ttt_win": int(parts[6]),
                            "download": int(parts[7]) if len(parts) > 7 else 0,
                            "report": int(parts[8]) if len(parts) > 8 else 0
                        }
    print(f"✅ Загружена статистика: {len(user_stats)} пользователей")

def save_stats():
    with open(STATS_FILE, 'w') as f:
        for uid, data in user_stats.items():
            f.write(f"{uid}|{uid}|{uid}|{data['admin_give']}|{data['admin_take']}|{data['fortune_win']}|{data['ttt_win']}|{data['download']}|{data['report']}\n")

def update_user_stat(uid, stat_name, amount):
    if uid not in user_stats:
        user_stats[uid] = {
            "admin_give": 0,
            "admin_take": 0,
            "fortune_win": 0,
            "ttt_win": 0,
            "download": 0,
            "report": 0
        }
    
    if stat_name in user_stats[uid]:
        user_stats[uid][stat_name] += amount
    save_stats()

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

# =============== КРЕСТИКИ-НОЛИКИ (ЛЁГКИЙ БОТ) ===============
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
    bot.send_message(uid, "❌ **Крестики-нолики с лёгким ботом**\n\nВыбери ставку (при победе x2):", parse_mode="Markdown", reply_markup=kb)

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
    
    ttt_games[uid] = {
        "board": board, 
        "turn": "user", 
        "bet": bet, 
        "message_id": None, 
        "chat_id": call.message.chat.id
    }
    
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
        add_coins(uid, win_amount)
        update_user_stat(uid, "ttt_win", win_amount)
        bot.edit_message_text(game_over_message("X", board, bet), chat_id, message_id, parse_mode="Markdown")
        del ttt_games[uid]
        bot.answer_callback_query(call.id, f"🎉 Ты выиграл {win_amount} монет!", show_alert=True)
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
            bot.answer_callback_query(call.id, f"😔 Ты проиграл {bet} монет", show_alert=True)
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
    bot.send_message(uid, f"🎰 **Колесо фортуны**\n\n💰 Твой баланс: {coins} монет\n\nВыбери ставку (шанс победы 50%):", parse_mode="Markdown", reply_markup=kb)

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
        add_coins(uid, win)
        update_user_stat(uid, "fortune_win", win)
        final_coins = get_coins(uid)
        
        result_text = f"🎉 **ПОБЕДА!** 🎉\n\n"
        result_text += f"💰 Ставка: {bet} монет\n"
        result_text += f"🏆 Выигрыш: {win} монет\n"
        result_text += f"💵 Чистый выигрыш: +{win - bet} монет\n"
        result_text += f"💰 Новый баланс: {final_coins} монет"
        
        bot.send_message(uid, result_text, parse_mode="Markdown")
    else:
        remove_coins(uid, bet)
        final_coins = get_coins(uid)
        
        result_text = f"😔 **ПРОИГРЫШ!** 😔\n\n"
        result_text += f"💰 Ставка: {bet} монет\n"
        result_text += f"💵 Потеряно: -{bet} монет\n"
        result_text += f"💰 Новый баланс: {final_coins} монет"
        
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
        types.InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        types.InlineKeyboardButton("🌐 Crack Plus", callback_data="crack_plus"),
        types.InlineKeyboardButton("🎰 Колесо фортуны", callback_data="fortune_wheel"),
        types.InlineKeyboardButton("❌ Крестики-нолики", callback_data="tic_tac_toe")
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
    add_coins(uid, 10)
    bot.send_message(uid, f"💰 +10 монет! Баланс: {get_coins(uid)}")

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📥 Crack Free", callback_data="download"),
        types.InlineKeyboardButton("🎯 Подробнее", callback_data="more"),
        types.InlineKeyboardButton("👥 Поделиться", callback_data="share"),
        types.InlineKeyboardButton("📢 Репорт", callback_data="report"),
        types.InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        types.InlineKeyboardButton("🌐 Crack Plus", callback_data="crack_plus"),
        types.InlineKeyboardButton("🎰 Колесо фортуны", callback_data="fortune_wheel"),
        types.InlineKeyboardButton("❌ Крестики-нолики", callback_data="tic_tac_toe")
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
        types.InlineKeyboardButton("💰 Выдать монеты", callback_data="admin_give_coins"),
        types.InlineKeyboardButton("💰 Забрать монеты", callback_data="admin_take_coins"),
        types.InlineKeyboardButton("📊 Логи действий", callback_data="admin_stats_log")
    )
    bot.send_message(m.chat.id, "🔧 Админ-панель", reply_markup=kb)

@bot.message_handler(commands=['cancel'])
def cancel(m):
    track_user(m)
    uid = m.from_user.id
    if uid in waiting_for_report:
        del waiting_for_report[uid]
        bot.reply_to(m, "❌ Отменено")

# =============== ПОКАЗ ЛОГОВ ДЕЙСТВИЙ (С ID ВМЕСТО ИМЕНИ) ===============
@bot.callback_query_handler(func=lambda call: call.data == "admin_stats_log")
def show_user_stats(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    
    bot.answer_callback_query(call.id)
    
    if not user_stats:
        bot.send_message(call.message.chat.id, "📊 Нет данных о действиях пользователей.")
        return
    
    sorted_users = sorted(user_stats.items(), key=lambda x: get_coins(x[0]), reverse=True)
    
    text = "📊 *Логи действий пользователей:*\n\n"
    
    for uid, data in sorted_users[:30]:
        balance = get_coins(uid)
        
        text += f"👤 *ID: {uid}*\n"
        text += f"   ✅ Выдано от админа: {data['admin_give']} монет\n"
        text += f"   ❌ Забрано админом: {data['admin_take']} монет\n"
        text += f"   🎰 Выигрыш в Фортуне: {data['fortune_win']} монет\n"
        text += f"   ❌⭕ Выигрыш в Крестиках: {data['ttt_win']} монет\n"
        text += f"   💰 Текущий баланс: {balance} монет\n\n"
    
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
    bot.send_message(uid, "🌐 **Crack Plus**\n\n💲 цена 60000 монет\n\nНапишите /buy чтобы купить!\n\nКоманда /start дает +10 монет к балансу!\n\nCrack Plus дает лучшую оптимизацию, гибкие настройки и больше функций!", parse_mode="Markdown")

# =============== ЗАБРАТЬ МОНЕТЫ (АДМИН) ===============
@bot.callback_query_handler(func=lambda call: call.data == "admin_take_coins")
def take_coins_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💰 Введите ID пользователя и количество монет через пробел\n\nПример: `123456789 500`\n(у пользователя будет списано указанное количество)", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_take_coins)

def process_take_coins(message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ Ошибка! Введите ID и сумму через пробел\nПример: `123456789 500`", parse_mode="Markdown")
            return
        
        user_id = int(parts[0])
        amount = int(parts[1])
        
        if amount < 1:
            bot.send_message(message.chat.id, "❌ Сумма должна быть больше 0!")
            return
        
        current_coins = get_coins(user_id)
        
        if current_coins < amount:
            bot.send_message(message.chat.id, f"❌ У пользователя `{user_id}` недостаточно монет!\n💰 Баланс: {current_coins} монет\n📤 Запрошено к списанию: {amount}", parse_mode="Markdown")
            return
        
        remove_coins(user_id, amount)
        update_user_stat(user_id, "admin_take", amount)
        bot.send_message(message.chat.id, f"✅ У пользователя `{user_id}` списано {amount} монет!\n💰 Новый баланс: {get_coins(user_id)}", parse_mode="Markdown")
        
        try:
            bot.send_message(user_id, f"💰 У вас списано {amount} монет администратором!\n💰 Ваш баланс: {get_coins(user_id)}")
        except:
            pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ Ошибка! Введите ID (число) и сумму (число)")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# =============== ВЫДАЧА МОНЕТ (АДМИН) ===============
@bot.callback_query_handler(func=lambda call: call.data == "admin_give_coins")
def give_coins_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", True)
        return
    
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "💰 Введите ID пользователя и количество монет через пробел\n\nПример: `123456789 500`\nСумма от 1 до 100000", parse_mode="Markdown")
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
        update_user_stat(user_id, "admin_give", amount)
        bot.send_message(message.chat.id, f"✅ Пользователю `{user_id}` выдано {amount} монет!\n💰 Баланс: {get_coins(user_id)}", parse_mode="Markdown")
        
        try:
            bot.send_message(user_id, f"💰 Вам начислено {amount} монет!\n💰 Ваш баланс: {get_coins(user_id)}")
        except:
            pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ Ошибка! Введите ID (число) и сумму (число)")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# =============== ОБРАБОТЧИК КНОПОК ===============
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
    
    # Исключения для КД
    if call.data not in ["balance", "crack_plus", "fortune_wheel", "fortune_10", "fortune_50", "fortune_100", "fortune_300", "fortune_5000", "fortune_10000", "tic_tac_toe", "ttt_bet_50", "ttt_bet_100", "ttt_bet_300", "ttt_bet_1000", "ttt_bet_2000", "ttt_bet_10000", "admin_give_coins", "admin_take_coins", "admin_stats_log"]:
        cd = check_cd(uid)
        if cd > 0:
            bot.answer_callback_query(call.id, f"⏳ {cd} сек!", True)
            return
        update_cd(uid)
    
    # Обработка кнопок
    if call.data == "download":
        global download_count
        download_count += 1
        update_user_stat(uid, "download", 1)
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
    
    elif call.data == "report":
        waiting_for_report[uid] = True
        bot.answer_callback_query(call.id)
        bot.send_message(uid, "✍️ Напишите текст жалобы (/cancel для отмены)")
    
    # Админ-кнопки
    elif is_admin(uid) and call.data.startswith('admin_') and call.data not in ["admin_give_coins", "admin_take_coins", "admin_stats_log"]:
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
    update_user_stat(uid, "report", 1)
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
    load_stats()
    print(f"✅ Загружено: {len(coins_data)} кошельков, {len(message_tracker)} в трекере, {len(blacklist)} в ЧС, {len(user_stats)} в статистике")
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
