import telebot
from telebot import types

TOKEN = "8773898221:AAGy67kpPvmxiHWCMagPdljvKWWX9fxz-FI"
SOFT_LINK = "https://www.mediafire.com/file/aulm7t7mu6388sc/zenin_crack.exe/file"

# ПРЯМАЯ ССЫЛКА НА КАРТИНКУ (замени на свою)
IMAGE_URL = "https://i.postimg.cc/4ykCrCCF/gg.jpg"  # <--- СЮДА ВСТАВЬ СВОЮ ССЫЛКУ

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton("📥 Скачать софт", callback_data="download")
    button2 = types.InlineKeyboardButton("🎯 Подробнее", callback_data="more")
    keyboard.add(button1, button2)
    
    bot.send_message(message.chat.id, "ВЫБИРАЙТЕ СОФТ", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "download":
        bot.send_message(call.message.chat.id, f"🔗 Ссылка для скачивания:\n{SOFT_LINK}")
    
    elif call.data == "more":
        # Отправляем картинку по ссылке
        bot.send_photo(
            call.message.chat.id, 
            IMAGE_URL, 
            caption="📌 Подробнее о софте:"
        )

print("✅ Бот запущен!")
bot.infinity_polling()
