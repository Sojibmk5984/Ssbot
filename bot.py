import telebot

# আপনার দেওয়া টোকেনটি এখানে বসানো হয়েছে
API_TOKEN = '8694471819:AAE8yRgfdOO2PHTpTrGD7vQmBVjU_PPG_B4'

bot = telebot.TeleBot(API_TOKEN)

# /start কমান্ড দিলে কী বলবে
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    bot.reply_to(message, f"আসসালামু আলাইকুম {user_name}!\nআমি আপনার নতুন বট। আমাকে যা লিখে পাঠাবেন, আমি তাই রিপ্লাই দিব।")

# সব মেসেজের উত্তর দেওয়া (Echo)
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"আপনি লিখেছেন: {message.text}")

print("বট সফলভাবে চালু হয়েছে...")
bot.infinity_polling()
