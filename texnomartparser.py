import requests
from bs4 import BeautifulSoup

from configs import database, cursor, CATEGORIES

class Parser:
    def __init__(self, page_name, category_id, max_products=10):
        self.page_name = page_name
        self.category_id = category_id
        self.max_products = max_products
        self.url = f'https://texnomart.uz/ru/katalog/{self.page_name}'
        self.host = f'https://texnomart.uz'

    def get_html(self, url):
        response = requests.get(url)
        try:
            response.raise_for_status()
            return response.text
        except Exception as e:
            print('Произошла ошибка')



    def get_data(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        product_links = [self.host + i.get('href') for i in soup.find_all('a', class_='product-name')]


        for link in product_links:
            product_page = self.get_html(link)
            soup2 = BeautifulSoup(product_page, 'html.parser')

            product_name = soup2.find('h1', class_='product__name').get_text(strip=True)
            print(product_name)
            product_price = soup2.find('div', class_='price__left').get_text(strip=True)
            product_photo =self.host + soup2.find('img', class_='swiper-slide__img')['src']
            characteristics = ''
            brand = ''
            product_details = soup2.find('ul', class_='characteristic__wrap').find_all('li', class_='characteristic__item')
            i = 0
            for stroke in product_details:
                if i == 0:
                    key, value = stroke.find('span', class_='characteristic__name'), stroke.find('span', class_='characteristic__value')
                    brand += f'{key.get_text(strip=True)} {value.get_text(strip=True)}'
                    i += 1
                else:
                    key, value = stroke.find('span', class_='characteristic__name'), stroke.find('span', class_='characteristic__value')
                    characteristics += f'{key.get_text(strip=True)} {value.get_text(strip=True)}\n'
            i = 0

            cursor.execute('''
            INSERT INTO products (product_title, brand, link, price, image, characteristics, category_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(product_title, link) DO NOTHING RETURNING *;
            ''', (product_name, brand, link, product_price, product_photo, characteristics, self.category_id))
            database.commit()
            cursor.execute('''SELECT * FROM products;
            ''')
            print(cursor.fetchall())


    def run(self):
        html = self.get_html(self.url)
        self.get_data(html)


def start_parser():
    for category_name, category_value in CATEGORIES.items():
        print('Парсим категорию - ', category_name)
        parser = Parser(page_name=category_value['page_name'], category_id=category_value['category_id'])
        parser.run()


#TODO Изменить так, чтобы добавлял все категории с сайта
def insert_categories():
    for category_name in CATEGORIES.keys():
        cursor.execute('''
        INSERT INTO categories(category_title) VALUES (%s)
        ON CONFLICT(category_title) DO NOTHING
        ''', (category_name,))

    database.commit()


insert_categories()
start_parser()
database.close()