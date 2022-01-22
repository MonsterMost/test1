import psycopg2 as sql

CATEGORIES = {
    'Оптимальные смартфоны': {
        'page_name': 'optimal-smartfony',
        'category_id': 1
    },
    'Игровые смартфоны': {
        'page_name': 'gaming-smartfony',
        'category_id': 2
    },
    'Флагманы': {
        'page_name': 'premium-smartfony',
        'category_id': 3
    }
}

TOKEN = '2050499280:AAFtc5Xxe3SYzW5kW_Ck-iCvOQaGBWXdvQ4'

DATA = {}

PAYME_TOKEN = '371317599:TEST:1638446514048'

MAX_QUANTITY = 3

# pip install BeautifulSoup4
# pip install requests
# pip install psycopg2
# pip install pytelegrambotapi

database = sql.connect(
    database='texnomartDenis',
    host='localhost',
    user='postgres',
    password='123456'
)


cursor = database.cursor()
