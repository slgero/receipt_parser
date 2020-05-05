"""Parse all data from the Perecrestok shop: `https://www.perekrestok.ru`."""
from time import sleep
from collections import namedtuple
import requests as req
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd


class Perecrestok:
    """Allow to parse all data about products from the Perecrestok."""

    def __init__(self):
        self.main_url = 'https://www.perekrestok.ru'
        self.url_catalog = 'https://www.perekrestok.ru/catalog'
        self.columns = [
            'Название',
            'Категория',
            'Производитель',
            'Торговая марка',
            'Вес',
            'Жирность'
        ]
        self.result = pd.DataFrame(columns=self.columns)

    def get_html(self, url: str)-> str:
        """Scroll HTML page and return HTML-code."""

        driver = webdriver.Chrome()
        driver.get(url)
        for i in range(0, 50000, 1080):
            driver.execute_script(f"window.scrollTo({i}, {i+1080})")
            sleep(3)
        page = driver.page_source
        driver.close()
        return page

    def get_product_name(self, soup: BeautifulSoup)-> str:
        """Return the porduct name."""

        name = soup.find(class_="js-product__title xf-product-card__title")
        if name:
            name = name.text.split('\n')[0]
        return name

    def error(self, function_name: str)-> None:
        """Raise error if status code not equal 200."""

        raise ValueError(f'Проблема с подключением к сети в функции {function_name}.')

    def get_catalog(self)-> set:
        """Return set of namedtuples about all categories in the catalog."""

        result = set()
        Category = namedtuple('Category', 'name url')

        resp = req.get(self.url_catalog)
        if resp.status_code != 200:
            self.error(self.get_catalog.__name__)
        soup = BeautifulSoup(resp.text, 'lxml')
        for cat in soup.find_all(class_="xf-catalog-categories__item"):
            href = cat.find(class_="xf-catalog-categories__link").get('href')
            name = cat.text.strip()
            result.add(Category(name, self.main_url + href))

        return result

    def parse_good(self, url: str)-> dict:
        """Parse information about the product."""

        product = dict()
        [product.setdefault(key, None) for key in self.columns]
        resp = req.get(url)
        if resp.status_code != 200:
            self.error(self.parse_good.__name__)
        soup = BeautifulSoup(resp.text, 'lxml')
        product['Название'] = self.get_product_name(soup)
        table = soup.find('table', attrs={'class':'xf-product-info__table xf-product-table'})
        if table:
            rows = table.find_all('tr')
            for row in rows:
                key = row.find_all(class_="xf-product-table__col-header")[0].text.strip()
                value = row.find_all('td')[0].text.strip()
                if key == 'Объём':
                    key = 'Вес'
                if key in self.columns:
                    product[key] = value
        return product

    def parse_category(self, category: namedtuple) -> pd.DataFrame:
        """Parse all products in the categoty."""

        print(f'Start parsing {category.name}.')
        page = self.get_html(category.url)
        soup = BeautifulSoup(page, 'lxml')
        goods = soup.find_all(class_='js-catalog-product _additionals xf-catalog__item')
        for good in goods:
            url = good.find(class_='xf-product-picture__link js-product__image').get('href')
            url = self.main_url + url
            product = self.parse_good(url)
            product['Категория'] = category.name
            self.result = pd.concat(
                [self.result, pd.DataFrame.from_dict(product, orient='index').T]
            )

        self.result = self.result.dropna(subset=['Название']).drop_duplicates(subset=['Название'])
        return self.result

    def parse_all(self):
        """Parse all product in `https://www.perekrestok.ru`."""

        for category in self.get_catalog():
            self.parse_category(category)
        return self.result
