import telebot;
bot = telebot.TeleBot('')
# Словарь для хранения ответов
responses = {
    "/start": "Здравствуй, мой дорогой друг! Представься.",
    "Данил": "Привет, Данил! Сколько тебе лет?",
    "Мне 14 лет": "Ты родился в 2010 году!",
    "/help": "Напиши 'Привет'",
    "Привет": "Здравствуй, мой дорогой друг! Представься."
}

@bot.message_handler(content_types=['text'])
def handle_message(message):
    text = message.text
    if text in responses:
        bot.send_message(message.from_user.id, responses[text])
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши '/help'.")

bot.polling(none_stop=True, interval=0)