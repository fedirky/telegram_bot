import telebot
from telebot import types
import sqlite3
from datetime import date
from data import *

database = sqlite3.connect('Shop.db', check_same_thread=False)

cursor = database.cursor()

bot = telebot.TeleBot(token)

comm = [types.BotCommand("start", "start bot"), types.BotCommand('help', 'список усіх команд'),
        types.BotCommand('info', 'загальна інформація'), types.BotCommand('support', 'виклик оператора'),
        types.BotCommand('make_order', 'почати замовлення'),
        types.BotCommand('price_list', 'список товарів')]

admin_id = 442112797

bot.set_my_commands(comm)

info = types.KeyboardButton('Про нас')
available_consoles = types.KeyboardButton('Прайс-лист')
make_order = types.InlineKeyboardButton('Почати замовлення')
support = types.KeyboardButton('Технічна підтримка')
main_keys = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
main_keys.add(info, make_order, support, available_consoles)
empty_keys = types.ReplyKeyboardMarkup()

consoles_keys = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
ps5 = types.KeyboardButton(consoles_array[0])
ps4 = types.KeyboardButton(consoles_array[1])
xbs = types.KeyboardButton(consoles_array[2])
xb1 = types.KeyboardButton(consoles_array[3])
ns = types.KeyboardButton(consoles_array[4])
consoles_keys.add(ps5, ps4, xbs, xb1, ns)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
                     'Вітання, {0.first_name}! Цей бот який допоможе Вам зробити замовлення.'
                     .format(message.from_user), reply_markup=main_keys)
    cursor.execute(f"SELECT ban_boolean FROM buyers WHERE telegram_id = '{message.from_user.id}'")
    data = cursor.fetchone()
    if data is None:
        get_registration(message)


def get_registration(message):
    msg = bot.send_message(message.chat.id, "Для початку користування нашим сервісом необхідно зареєструватися.\n"
                                            "У випадку якщо ви ввели некоректні дані, ви зможете їх змінити"
                                            "\n\nБудь ласка, введіть Ваше ПІБ:", reply_markup=empty_keys)
    bot.register_next_step_handler(msg, get_registration2)


def get_registration2(message):
    if message.text in menu_text:
        get_registration(message)
    else:
        full_name = message.text
        msg = bot.send_message(message.chat.id, "Тепер введіть Ваш номер телефону:", reply_markup=empty_keys)
        bot.register_next_step_handler(msg, get_registration3, full_name)


def get_registration3(message, full_name):
    if message.text in menu_text:
        get_registration2(message)
    else:
        phone_number = message.text
        msg = bot.send_message(message.chat.id, "Тепер введіть адресу Вашої поштової скриньки:",
                               reply_markup=empty_keys)
        bot.register_next_step_handler(msg, get_registration4, full_name, phone_number)


def get_registration4(message, full_name, phone_number):
    if message.text in menu_text:
        get_registration3(message, full_name)
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        yes = types.KeyboardButton('Так')
        no = types.KeyboardButton('Ні')
        mail_address = message.text
        markup.add(yes, no)
        msg = bot.send_message(message.chat.id, f"Ваш ПІБ:\n{full_name}\n"
                                                f"Номер телефону:\n{phone_number}\n"
                                                f"Поштова адреса:\n{mail_address}\n\nЧи все вірно?",
                               reply_markup=markup)
        bot.register_next_step_handler(msg, get_registration5, full_name, phone_number, mail_address)


def get_registration5(message, full_name, phone_number, mail_address):
    if message.text == 'Так':
        cursor.execute(
            f"INSERT INTO buyers (full_name, phone_number, telegram_id, mail_address,ban_boolean)"
            f"VALUES('{full_name}', '{phone_number}', '{message.from_user.id}', '{mail_address}', 'f')")
        bot.send_message(message.chat.id, "Дякуємо, Ви успішно пройшли реєстрацію.\n\n",
                         reply_markup=main_keys)
        database.commit()
    elif message.text == 'Ні':
        get_registration(message)
    else:
        get_registration5(message, full_name, phone_number, mail_address)


@bot.message_handler(commands=['support'])
def get_support(message):
    msg = bot.send_message(message.chat.id, "Будь ласка, впишіть Ваше питання наступним повідомленням. "
                                            "Оператор нашого сервісу зв'яжеться з Вами найближчим часом :)")
    bot.register_next_step_handler(msg, get_support2, message.from_user.id)


def get_support2(message, user_id):
    if message.text in menu_text:
        get_support(message)
    else:
        bot.send_message(message.chat.id, "Дякуємо, ми прийняли ваш запит")
        bot.send_message(admin_id, f'Клієнт очікує на допомогу: {message.text} \n ID Клієнта: {user_id}')


@bot.message_handler(commands=['company_info'])
def get_company_info(message):
    bot.send_message(message.chat.id, info_placeholder)


@bot.message_handler(commands=['price_list'])
def get_price_list(message):
    msg = bot.send_message(message.chat.id, 'Оберіть модель консолі аби дізнатися ціну на її оренду:'
                           .format(message.from_user), reply_markup=consoles_keys)
    bot.register_next_step_handler(msg, get_price_list2)


def get_price_list2(message):
    if message.text in consoles_array:
        cursor.execute(
            f"SELECT name, producer, price, rent_price FROM console_models WHERE name = '{message.text}'")
        records = cursor.fetchmany(4)
        name = records[0][0]
        producer = records[0][1]
        price = records[0][2]
        rent_price = records[0][3]
        bot.send_message(chat_id=message.chat.id,
                         text=f"Консоль {name} від виробника {producer}\n Застава: {int(price/3)} Гривень\n"
                              f"Орендна плата починається з {rent_price} Гривень в день.", reply_markup=main_keys)
    else:
        get_price_list(message)


def get_start_order(message):
    cursor.execute(f"SELECT ban_boolean, full_name FROM buyers WHERE telegram_id = '{message.from_user.id}'")
    data = cursor.fetchmany(2)
    if data[0][0] == 'f':
        bot.send_message(message.chat.id,
                         f"Дякуємо за довіру, Ваше замовлення буде оформлене на клієнта з іменем {data[0][1]}.")
        get_console(message)
    elif data[0][0] == 't':
        bot.send_message(message.chat.id, 'Вибачте, однак наразі всі консолі недоступні.'
                                          '\nСпробуйте пізніше \u2639', reply_markup=empty_keys)


def get_console(message):
    msg = bot.send_message(message.chat.id, 'Оберіть консоль із списку можливих:', reply_markup=consoles_keys)
    bot.register_next_step_handler(msg, get_console2)


def get_console2(message):
    if message.text in consoles_array:
        console_model = message.text
        bot.send_message(chat_id=message.chat.id,
                         text=f'Чудово, Ви вибрали консоль наступної моделі: {console_model}',
                         reply_markup=None)
        try:
            cursor.execute(f"SELECT console_id FROM consoles WHERE"
                           f" console_model_id = '{consoles_array.index(message.text) + 1}'and available_boolean = 't'")
            data = cursor.fetchone()[0]
            # print(data)
            get_game(message, console_model)
        except TypeError:
            bot.send_message(chat_id=message.chat.id,
                             text=f'Але нажаль такої моделі зараз немає на складі \U0001f622',
                             reply_markup=main_keys)
    else:
        get_console(message)


def get_game(message, console_model):
    msg = bot.send_message(message.chat.id, 'Введіть назву однієї або двох ігор одним повідомленням:',
                           reply_markup=main_keys)
    bot.register_next_step_handler(msg, get_game2, console_model)


def get_game2(message, console_model):
    if message.text in menu_text:
        get_game(message, console_model)
    else:
        game = message.text
        bot.send_message(message.chat.id, f'Отже, Ви обрали такі гру/ігри: {game}')
        get_time(message, console_model, game)


def get_time(message, console_model, game):
    markup = types.ReplyKeyboardMarkup(row_width=1)
    seven = types.KeyboardButton('7 днів')
    fourteen = types.KeyboardButton('14 днів, 20% знижка')
    month = types.KeyboardButton('Місяць, 30% знижка')
    markup.add(seven, fourteen, month)
    msg = bot.send_message(message.chat.id, 'Оберіть тривалість аренди: ', reply_markup=markup)
    bot.register_next_step_handler(msg, get_time2, console_model, game)


def get_time2(message, console_model, game):
    if message.text != '7 днів' and message.text != '14 днів, 20% знижка' and message.text != 'Місяць, 30% знижка':
        get_time(message, console_model, game)
    else:
        time = 0
        if message.text == '7 днів':
            time = 7
        if message.text == '14 днів, 20% знижка':
            time = 14
        if message.text == 'Місяць, 30% знижка':
            time = 30
        bot.send_message(chat_id=message.chat.id, text=f'Ви арендуєте консоль на {time} днів', reply_markup=None)
        get_delivery_type(message, console_model, game, time)


def get_delivery_type(message, console_model, game, time):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    now = types.KeyboardButton(delivery_array[0])
    then = types.KeyboardButton(delivery_array[1])
    markup.add(now, then)
    msg = bot.send_message(message.chat.id, 'Оберіть варіант доставки: ', reply_markup=markup)
    bot.register_next_step_handler(msg, get_delivery_type2, console_model, game, time)


def get_delivery_type2(message, console_model, game, time):
    if message.text != delivery_array[0] and message.text != delivery_array[1]:
        get_delivery_type(message, console_model, game, time)
    else:
        delivery_info = message.text
        if delivery_info == delivery_array[0]:
            bot.send_message(chat_id=message.chat.id, text=f'Ви обрали {delivery_info}.', reply_markup=None)
            get_payment(message, console_model, game, time, delivery_info)
        elif delivery_info == delivery_array[1]:
            msg = bot.send_message(chat_id=message.chat.id,
                                   text='Напишіть будь-ласка одним повідомленням номер зручного '
                                        'Вам відділення Нової Пошти та назву міста де воно '
                                        'знаходиться:', reply_markup=main_keys)
            bot.register_next_step_handler(msg, get_delivery_address, console_model, game, time)


def get_delivery_address(message, console_model, game, time):
    if message.text in menu_text:
        msg = bot.send_message(chat_id=message.chat.id,
                               text='Напишіть будь-ласка одним повідомленням номер зручного '
                                    'Вам відділення Нової Пошти та назву міста де воно '
                                    'знаходиться:', reply_markup=main_keys)
        bot.register_next_step_handler(msg, get_delivery_address, console_model, game, time)
    else:
        delivery_address = message.text
        bot.send_message(chat_id=message.chat.id, text=f'Ви ввели: {delivery_address}', reply_markup=None)
        get_payment(message, console_model, game, time, delivery_address)


def get_payment(message, console_model, game, time, delivery_info):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    now = types.KeyboardButton('Зараз картою онлайн')
    then = types.KeyboardButton('При отриманні')
    markup.add(now, then)
    msg = bot.send_message(message.chat.id, 'А тепер оберіть варіант оплати: ', reply_markup=markup)
    bot.register_next_step_handler(msg, get_payment2, console_model, game, time, delivery_info)


def get_payment2(message, console_model, game, time, delivery_info):
    if message.text != 'При отриманні' and message.text != 'Зараз картою онлайн':
        get_payment(message, console_model, game, time, delivery_info)
    else:
        payment_status = message.text
        if payment_status == 'При отриманні':
            bot.send_message(chat_id=message.chat.id,
                             text=f'Дякуємо, оплата відбудеться при отриманні замовлення, '
                                  f'не забудьте гаманець вдома \U0001f605', reply_markup=main_keys)
            get_order_result(message, console_model, game, time, delivery_info, payment_status)
        if payment_status == 'Зараз картою онлайн':
            get_payment3(message, console_model, game, time, delivery_info, payment_status)


def get_payment3(message, console_model, game, time, delivery_info, payment_status):
    bot.send_message(chat_id=message.chat.id, text='Дякуємо, оплата відбудеться пілся оформлення замовлення.\n'
                                                   'У вас буде пів години аби провести оплату',
                     reply_markup=main_keys)
    get_order_result(message, console_model, game, time, delivery_info, payment_status)


def get_order_result(message, console_model, game, duration, delivery_info, payment_status):
    cursor.execute(f"SELECT rent_price FROM console_models WHERE console_model_id = "
                   f"'{consoles_array.index(console_model) + 1}'")
    price = cursor.fetchone()[0]

    price = price * duration
    if duration == 14:
        price = int(price * 0.8)
    if duration == 30:
        price = int(price * 0.7)
    txt = f"Модель консолі: {console_model}\nІгри: {game} \nТривалість оренди: {duration} днів\nІнформація щодо " \
          f"доставки: {delivery_info}\nОплата: {payment_status}\nЦіна замовлення:{price} Гривень\n\nВсе вірно?"
    yes = types.KeyboardButton('Так')
    no = types.KeyboardButton('Ні')
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(yes, no)
    msg = bot.send_message(chat_id=message.chat.id, text=txt, reply_markup=markup)
    bot.register_next_step_handler(msg, get_order_result2, console_model, game,
                                   duration, delivery_info, payment_status, txt, price)


def get_order_result2(message, console_model, game, duration, delivery_info, payment_status, txt, price):
    if message.text == 'Так':
        try:
            cursor.execute(f"SELECT console_id FROM consoles WHERE console_model_id = "
                           f"'{consoles_array.index(console_model) + 1}'and available_boolean = 't'")
            console_id = cursor.fetchone()[0]
            cursor.execute(f"UPDATE consoles SET available_boolean = 'f' WHERE console_id = '{console_id}'")
            database.commit()

            d = date.today()
            cursor.execute(
                f"INSERT INTO orders (buyer_telegram_index, console_id, order_date, order_duration, order_price,"
                f" payment_status, delivery_address) VALUES('{message.from_user.id}', '{console_id}', '{d}', "
                f"'{duration}', '{price}', '{payment_status}', '{delivery_info}')")
            database.commit()
            order_rowid = cursor.lastrowid
            bot.send_message(chat_id=message.chat.id, text="Дякуємо, Ваше замовлення було прийняте на обробку.",
                             reply_markup=main_keys)
            if payment_status == 'При отриманні':
                bot.send_message(chat_id=admin_id, text=txt + "\nRowid:" + str(order_rowid), reply_markup=main_keys)
            elif payment_status == 'Зараз картою онлайн':
                get_payment_link(message, order_rowid, txt)

        except TypeError:
            bot.send_message(chat_id=message.chat.id,
                             text=f'Але нажаль такої моделі зараз немає на складі \U0001f622',
                             reply_markup=main_keys)
    elif message.text == 'Ні':
        bot.send_message(chat_id=message.chat.id, text=f'Тоді повторіть процес замовлення спочатку та будьте '
                                                       f'уважнішими \U0001f609', reply_markup=main_keys)
    else:
        get_order_result(message, console_model, game, duration, delivery_info, payment_status)


def get_payment_link(message, order_rowid, txt):
    # TODO : ЗРОБИТИ НОРМАЛЬНУ ОПЛАТУ
    bot.send_message(chat_id=admin_id, text=txt + "\nRowid:" + str(order_rowid), reply_markup=main_keys)


@bot.message_handler(content_types=['text'])
def bot_message(message):
    if message.text == 'Технічна підтримка':
        get_support(message)
    elif message.text == 'Почати замовлення':
        get_start_order(message)
    elif message.text == 'Прайс-лист':
        get_price_list(message)
    elif message.text == 'Про нас':
        get_company_info(message)


bot.polling(none_stop=True)
