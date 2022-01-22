from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from configs import CATEGORIES


def generate_phone_number():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = KeyboardButton(text='Отправить мой номер телефона', request_contact=True)
    markup.add(btn)
    return markup


def generate_categories():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    cartButton = KeyboardButton(text='Корзина')  # U0001F6D2
    buttons = []
    for category_name in CATEGORIES.keys():
        btn = KeyboardButton(text=category_name)
        buttons.append(btn)
    markup.add(*buttons, cartButton)
    return markup


def generate_pagination(pages, current_page=1):
    keyboard = InlineKeyboardMarkup()
    first_btn = InlineKeyboardButton(text='\U000023EA', callback_data='1')
    prev_btn = InlineKeyboardButton(text='\U000025C0', callback_data=str(current_page - 1))
    current_btn = InlineKeyboardButton(text=str(current_page), callback_data=str(current_page))
    next_btn = InlineKeyboardButton(text='\U000025B6', callback_data=str(current_page + 1))
    last_btn = InlineKeyboardButton(text='\U000023E9', callback_data=str(pages))

    if 3 <= current_page < pages - 1 and pages > 4:
        keyboard.row(first_btn, prev_btn, current_btn, next_btn, last_btn)

    elif current_page == pages and  pages > 2:
        keyboard.row(first_btn, prev_btn, current_btn)

    elif current_page == 1 and pages == 2:
        keyboard.row(current_btn, next_btn)

    elif current_page == 2 and pages == 2:
        keyboard.row(prev_btn, current_btn)

    elif current_page == 1 and pages > 2:
        keyboard.row(current_btn, next_btn, last_btn)

    elif current_page == 2 and pages > 4:
        keyboard.row(prev_btn, current_btn, next_btn, last_btn)

    elif current_page == pages - 1 and pages > 4:
        keyboard.row(first_btn, prev_btn, current_btn, next_btn)
    return keyboard


def generate_detail_markup(link, product_id, price):
    keyboard = InlineKeyboardMarkup()
    link_btn = InlineKeyboardButton(text='Подробнее', url=link)
    buy_btn = InlineKeyboardButton(text='В корзину', callback_data=f'add_{product_id}_{price}')
    keyboard.add(link_btn, buy_btn)
    return keyboard

def generate_cart_menu(cart_id):
    keyboard = InlineKeyboardMarkup()
    pay_btn = InlineKeyboardButton(text='Оплатить', callback_data=f'pay_{cart_id}')
    keyboard.add(pay_btn)
    return keyboard