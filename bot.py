import telebot;
bot = telebot.TeleBot('8157150834:AAEHXAGHI_dPYxo4IbpN7Bgm5FpSqmnc004');
@bot.message_handler(content_types=['text']) # слушаем бота
def get_text(message):
    if message.text == "/start": 
         bot.send_message(message.from_user.id,"здравствуй,мой дорогой друг!Представтесь")
    if message.text == "Данил": 
         bot.send_message(message.from_user.id,"Привет Данил! сколько тебе лет?")
    elif message.text == "Мне 14 лет":      
         bot.send_message(message.from_user.id,"ты родился в 2010 году!")
    elif message.text == "/help":    
        bot.send_message(message.from_user.id, "Напиши привет")
    elif message.text == "Привет":
        bot.send_message(message.from_user.id,"здравствуй,мой дорогой друг!Представтесь")
    else:
        bot.send_message(message.from_user.id, "я тебя не понимаю '/help'")
bot.polling(none_stop=True, interval=0)