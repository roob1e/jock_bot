import telebot
import sqlite3
from telebot import types
from openai import OpenAI

openai = OpenAI(api_token='токен')  # Укажите ваш ключ API OpenAI здесь
bot = telebot.TeleBot('токен')  #  Укажите токен вашего бота

markup1 = types.InlineKeyboardMarkup(row_width=1)
item1_1 = types.InlineKeyboardButton(text='Начать', callback_data='start_')
markup1.add(item1_1)

markup2 = types.InlineKeyboardMarkup(row_width=1)
item2_1 = types.InlineKeyboardButton(text='Упражнения (GPT-3.5)', callback_data='exercises')
item2_2 = types.InlineKeyboardButton(text='План', callback_data='plan')
item2_3 = types.InlineKeyboardButton(text='Статистика', callback_data='stats')
markup2.add(item2_1, item2_2, item2_3)

markup3 = types.InlineKeyboardMarkup(row_width=1)
item3_1 = types.InlineKeyboardButton(text='Вернуться в меню', callback_data='stop_gen')
markup3.add(item3_1)

@bot.message_handler(commands=['start'])
def get_start(message):
    user_id = message.chat.id

    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                premium BOOL NOT NULL
        )
    ''')
    
    cursor.execute("SELECT id FROM Users WHERE id=?", (user_id,))
    exists = cursor.fetchall()

    if not exists:
        bot.send_message(message.chat.id, 'Привет! Нажми на кнопку "Начать".', reply_markup=markup1)
    else:
        call_name = cursor.execute("SELECT name FROM Users WHERE id=?", (user_id,)).fetchone()
        if call_name:
            call_name = call_name[0]
            print(call_name)
            bot.send_message(message.chat.id, f'Привет, {call_name}! Чем займёмся сегодня?', reply_markup=markup2)

    connection.close()

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == 'start_':
        bot.send_message(call.message.chat.id, 'Привет! Напиши своё имя:')
        bot.register_next_step_handler(call.message, get_name)

    elif call.data == 'exercises':
        bot.send_message(call.message.chat.id, 'ПОМНИ!')
        bot.send_message(call.message.chat.id, 'Мы не несём ответственность за возможные ошибки при генерации! Вы используете эту функцию на свой страх и риск.\n Продолжая пользоваться данным ботом, вы соглашаетесь с вышеуказанным текстом.')
        bot.register_next_step_handler(call.message, generate_exercises_mid)

    elif call.data == 'stop_gen':
        bot.register_next_step_handler(call.message, get_start)

def get_name(message):
    user_id = message.chat.id
    global name 
    name = message.text
    bot.send_message(user_id, f'Привет, {name}! Добро пожаловать! Введи свой возраст:')
    bot.register_next_step_handler(message, get_age)

def get_age(message):
    user_id = message.chat.id
    age = message.text

    if not age.isdigit():
        bot.send_message(user_id, 'Пожалуйста, введите корректный возраст (целое число).')
        bot.register_next_step_handler(message, get_age)
        return

    bot.send_message(user_id, f'Спасибо, {name.strip()}, за предоставленную информацию!')

    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()

    cursor.execute('''
        INSERT INTO Users (id, name, age) VALUES (?, ?, ?)''', (user_id, name.strip(), int(age),)
        )

    connection.commit()
    connection.close()

@bot.message_handler(content_types=['text'])
def generate_exercises_mid(message):
    bot.send_message(message.chat.id, 'Введите запрос: ')
    bot.register_next_step_handler(message, generate_exercises)

@bot.message_handler(content_types=['text'])
def generate_exercises(message):
    response_AI = generate(message.text)
    bot.send_message(message.chat.id, text=response_AI, reply_markup=markup3)
    bot.register_next_step_handler(message, generate_exercises_mid)

def generate(prompt):
    response = openai.chat.completions.create(
        model='gpt-3.5-turbo', 
        messages=[
            {"role": "system", "content": "Ты - ИИ, помогающий людям"},
            {"role": "user", "content": f"{prompt}"}
        ]
    ).choices[0].message

    return response

bot.polling()