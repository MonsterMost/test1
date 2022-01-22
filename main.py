from telebot import TeleBot
from configs import *
from keyboards import *
from functions import *
from texnomartparser import start_parser
from telebot.types import LabeledPrice
bot = TeleBot(TOKEN, parse_mode='HTML')


@bot.message_handler(commands=['start'])
def command_start(message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name

    msg_for_user = f'''Привет {first_name}
Это тестовый бот
Здесь вы можете посмотреть товары'''
    msg = bot.send_message(chat_id, msg_for_user, reply_markup=generate_phone_number())

    cursor.execute('''SELECT * FROM users WHERE telegram_id = %s''', (chat_id,))
    user = cursor.fetchone()

    if not user:
        bot.register_next_step_handler(msg, register_user)
    else:
        choose_category(message)


def register_user(message):
    chat_id = message.chat.id
    try:
        phone = message.contact.phone_number
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        # Регистрация пользователя
        cursor.execute('''
        INSERT INTO users (telegram_id, first_name, last_name, phone) VALUES (%s, %s, %s, %s)
        ON CONFLICT (telegram_id) DO NOTHING
        ''', (chat_id, first_name, last_name, phone))
        # Создание корзины пользователя

        cursor.execute('''
        INSERT INTO cart (user_id) SELECT user_id FROM users WHERE telegram_id = %s 
        ON CONFLICT(user_id) DO NOTHING
        ''', (chat_id,))
        database.commit()
        choose_category(message)

    except:
        msg = bot.send_message(chat_id, 'НАЖМИТЕ НА КНОПКУ!!!', reply_markup=generate_phone_number())
        bot.register_next_step_handler(msg, register_user)


def choose_category(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, 'Выберите категорию', reply_markup=generate_categories())
    bot.register_next_step_handler(msg, show_category)

@bot.message_handler(regexp=r'[а-яА-Яё]+')
def show_category(message):
    chat_id = message.chat.id
    category_name = message.text
    if 'корзина' in category_name.lower():
        show_cart(message)

    if category_name in CATEGORIES:
        category_id = CATEGORIES[category_name]['category_id']
        '''Получение общего количества товаров'''
        cursor.execute('''
        SELECT COUNT(*) FROM products WHERE category_id = %s
        ''', (category_id,))
        DATA['count_products'] = cursor.fetchone()[0]
        DATA['total_pages'] = get_total_pages(DATA['count_products'], MAX_QUANTITY)
        DATA['category_name'] = category_name

        """Получение инфы о товарах"""
        cursor.execute('''
        SELECT product_id, product_title, price FROM products WHERE category_id = %s
        ''', (category_id,))
        DATA['products'] = cursor.fetchall()

        if DATA['products']:
            pagination_products(message)
        else:
            bot.send_message(chat_id, 'Ничего не найдено')


def pagination_products(message):
    chat_id = message.chat.id
    user_text = f'Список продуктов в категории {DATA["category_name"]} \n\n'
    i = 1
    for product in DATA['products'][0:MAX_QUANTITY]:
        product_id = product[0]
        title = product[1]
        price = product[2]

        user_text += f'''{i}. {title}
Стоимость: {price}
Подробнее: /product_{product_id}\n\n'''
        i += 1
    bot.send_message(chat_id, user_text, reply_markup=generate_pagination(DATA['total_pages']))


@bot.callback_query_handler(func=lambda call: call.data.isdigit())
def answer_page_call(call):
    chat_id = call.message.chat.id
    message_id = call.message.id
    current_page = int(call.data)

    try:
        user_text = f'Список продуктов в категории {DATA["category_name"]} \n\n'
        start = (current_page - 1) * MAX_QUANTITY
        last_index = current_page * MAX_QUANTITY

        end = last_index if last_index <= DATA['count_products'] else DATA['count_products']

        for i in range(start, end):
            product_id = DATA['products'][i][0]
            title = DATA['products'][i][1]
            price = DATA['products'][i][2]
            user_text += f'''{i + 1}. {title}
Стоимость: {price}
Подробнее: /product_{product_id}\n\n'''
        bot.edit_message_text(text=user_text, chat_id=chat_id,
                              message_id=message_id,
                              reply_markup=generate_pagination(DATA['total_pages'], current_page)
                              )
        bot.answer_callback_query(call.id, show_alert=False)
    except Exception as e:
        print(f'{e.__class__.__name__}: {e}')
        bot.answer_callback_query(call.id, 'Текущая страница')


@bot.message_handler(regexp=r'\/product_[0-9]+')
def show_show_product_detail(message):
    chat_id = message.chat.id
    _, product_id = message.text.split('_')

    cursor.execute(
        '''
        SELECT product_title, brand, link, price, image, characteristics FROM products
        WHERE product_id = %s
        ''', (product_id,)
    )
    product = cursor.fetchone()

    if product:
        title = product[0]
        brand = product[1]
        link = product[2]
        price = product[3]
        image = product[4]
        characteristics = product[5]
        msg_for_user = f'''<b>{title}</b>
<b>{brand}</b>
<b>Описание товара</b>
<i>{characteristics}</i>
<b>Стоимость: </b>{price}

'''
        markup = generate_detail_markup(link=link, product_id=product_id, price=price)
        bot.send_photo(chat_id, photo=image, caption=msg_for_user, reply_markup=markup)
    else:
        bot.send_message(chat_id, 'Продукт не найден')


@bot.callback_query_handler(func=lambda call: 'add' in call.data)
def add_product_in_cart(call):
    _, product_id, product_price = call.data.split('_')
    chat_id = call.message.chat.id

    # Получить данные о корзине
    cursor.execute('''
    SELECT cart_id FROM cart WHERE user_id = (
        SELECT user_id FROM users WHERE telegram_id = %s
    )
    ''', (chat_id,))
    cart_id = cursor.fetchone()
    product_price = product_price.replace(' ', '')
    # Добавление товара в корзину

    cursor.execute('''
    INSERT INTO cart_products (cart_id, product_id, price) 
    VALUES (%(cart_id)s, %(product_id)s, %(price)s )
    ON CONFLICT (cart_id, product_id) DO UPDATE
    SET price = cart_products.price + %(price)s,
    quantity = cart_products.quantity + 1
    WHERE cart_products.cart_id = %(cart_id)s AND cart_products.product_id = %(product_id)s;
    
    UPDATE cart
    SET total_price = info.total_price,
    total_quantity = info.total_quantity
    FROM (SELECT SUM(quantity) as total_quantity, SUM(price) as total_price FROM cart_products
    WHERE cart_id = %(cart_id)s) as info;
    
    ''', {
        'cart_id': cart_id,
        'product_id': product_id,
        'price': product_price
    })
    database.commit()
    bot.answer_callback_query(callback_query_id=call.id, text='Добавлено')


@bot.message_handler(func=lambda message: 'корзина' in message.text.lower())
def show_cart(message):
    chat_id = message.chat.id
    """Получение всех продуктов"""
    cursor.execute('''
    SELECT product_title, cart_products.quantity, cart_products.price FROM cart_products
    JOIN products USING(product_id)
    WHERE cart_id = (SELECT cart_id FROM cart WHERE user_id = (
        SELECT user_id FROM users WHERE telegram_id = %s
        )
    )
    ''', (chat_id,))
    products = cursor.fetchall()
    cursor.execute('''
    SELECT cart_id, total_price, total_quantity FROM cart
    WHERE user_id = ( SELECT user_id FROM users WHERE telegram_id = %s )
    
    ''', (chat_id,))

    cart_id, total_price, total_quantity = cursor.fetchone()

    cart_text = "Ваша корзина.\n"
    i = 0
    for title, quantity, price in products:
        i+=1
        cart_text += f'''{i}. <strong>{title}</strong>
Кол-во: {quantity}
Стоимость: {price} сум\n\n'''

    cart_text += f'''<i>Общее кол-во товаров в корзине: {total_quantity}</i>
<i>Общая стоимость корзины: {total_price} сум</i>
Очистить корзину - /clear_cart'''
    bot.send_message(chat_id, cart_text, reply_markup=generate_cart_menu(cart_id))

@bot.message_handler(commands=['clear_cart'])
def cleaned_cart(message):
    chat_id = message.chat.id

    cursor.execute('''
    DELETE FROM cart_products WHERE cart_id = (SELECT cart_id FROM cart WHERE user_id =
    (SELECT user_id FROM users WHERE telegram_id = %s)
    );
    UPDATE cart
    SET total_price = 0,
    total_quantity = 0;
    ''', (chat_id,))
    database.commit()
    bot.send_message(chat_id, 'Корзина успешно очищена!')


@bot.callback_query_handler(func=lambda call: 'pay' in call.data)
def pay_cart(call):
    _, cart_id = call.data.split('_')  # pay_14   _='pay' cart_id = 14
    chat_id = call.message.chat.id

    cursor.execute(
        """
        SELECT total_price FROM cart WHERE cart_id = %s
        """, (cart_id,)
    )
    total_price = int(cursor.fetchone()[0])

    # Получим все товары из корзины
    cursor.execute(
        """
        SELECT product_title, cart_products.quantity, cart_products.price
        FROM cart_products
        JOIN products USING(product_id)
        WHERE cart_id = %s
        """, (cart_id,)
    )
    products = cursor.fetchall()

    invoice_desc = 'Вы выбрали: \n\n'
    i = 0
    for title, quantity, price in products:
        i += 1
        invoice_desc += f'''{i}. {title}
        Кол-во: {quantity}
        Стоимость: {price} сум\n\n'''

    INVOICE = {
        "chat_id": chat_id,
        "title" : 'Ваша корзина',
        "description": invoice_desc,
        'invoice_payload': 'bot-defined invoice payload',
        'provider_token': PAYME_TOKEN,
        'currency': 'UZS',
        'prices': [LabeledPrice(label='Корзина', amount=int(str(total_price)+ '00') )],
        'start_parameter': 'pay',
        'is_flexible': False
    }


    try:
        bot.send_invoice(**INVOICE) #Kwargs
    except Exception:
        bot.send_message(chat_id, 'Не удалось провести оплату.')



bot.polling(none_stop=True)
