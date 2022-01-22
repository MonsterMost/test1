import requests
from bs4 import BeautifulSoup

from configs import database, cursor, CATEGORIES

class Parser:
    def __init__(self, page_name, category_id, max_product=10):
        self.url = f'https://texnomart.uz/ru/katalog/{page_name}'
        self.host = 'https://texnomart.uz'
        self.max_product = max_product
        self.category_id = category_id

    def get_html(self, url):
        response = requests.get(url)
        try:
            response.raise_for_status() # Проверит статус ответа
            return response.text
        except Exception as e:
            print(f'Произошла ошибка {e}')


    def get_data(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        product_links = [self.host + i.find('a', class_='name').get('href') for i in soup.find_all('div', class_='proporties')]

        for link in product_links:
            product_page = self.get_html(link)
            soup2 = BeautifulSoup(product_page, 'html.parser')
            product_name = soup2.find('h1', class_='title').get_text(strip=True)
            product_price = soup2.find('span', class_='price').get_text(strip=True).replace(' cумc учетом НДС', '')
            product_photo = self.host + soup2.find('a', class_='swiper-slide')['href']
            characteristics = ''
            brand = ''
            product_table = soup2.find('tbody', class_='row').find_all('tr', class_='col-sm-6')
            i = 0
            for row in product_table:
                if i == 0:
                    key, value = row.find_all('td') # Их все равно 2 и спокойно перекачиваем в 2 переменные
                    brand += f'{key.get_text(strip=True)} {value.get_text(strip=True)}'
                    i+=1
                else:
                    key, value = row.find_all('td')  # Их все равно 2 и спокойно перекачиваем в 2 переменные
                    characteristics += f'{key.get_text(strip=True)} {value.get_text(strip=True)}\n'
            i = 0

            cursor.execute('''
            INSERT INTO products (product_title, brand, link, price, image, characteristics, category_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT(product_title, link) DO NOTHING            
            ''', (product_name, brand, link, product_price, product_photo, characteristics, self.category_id))
            database.commit()
        return True



    def run(self):
        html = self.get_html(self.url)
        status = self.get_data(html)
        if status:
            print('Данные успешно сохранены')



def start_parser():
    for category_name, category_value in CATEGORIES.items():
        print(f'Парсим категорию - {category_name}')
        parser = Parser(page_name=category_value['page_name'], category_id=category_value['category_id'])
        parser.run()


def insert_categories():
    for category_name in CATEGORIES.keys():
        cursor.execute('''
        INSERT INTO categories(category_title) VALUES (%s) ON CONFLICT(category_title) DO NOTHING
        ''', (category_name,))
        database.commit()



insert_categories()
start_parser()

database.close()


