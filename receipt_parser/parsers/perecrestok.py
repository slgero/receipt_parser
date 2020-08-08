"""Parse info about Perecrestok supremarket: `https://www.perekrestok.ru`."""
from time import sleep
from typing import Dict, Optional, NamedTuple, Set, NoReturn
import requests as req
from selenium import webdriver  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
import pandas as pd  # type: ignore

Category = NamedTuple("Category", [("name", str), ("url", str)])


class Perecrestok:
    """Allow to parse all data about products from the Perecrestok."""

    def __init__(self):
        self.main_url = "https://www.perekrestok.ru"
        self.url_catalog = "https://www.perekrestok.ru/catalog"
        self.columns = [
            "Название",
            "Категория",
            "Производитель",
            "Торговая марка",
            "Вес",
            "Жирность",
        ]
        self.result = pd.DataFrame(columns=self.columns)

    @staticmethod
    def __get_html(url: str) -> str:
        """Scroll down a HTML page and return the HTML-code."""

        driver = webdriver.Chrome()
        driver.get(url)
        for i in range(0, 50000, 1080):
            driver.execute_script(f"window.scrollTo({i}, {i+1080})")
            sleep(3)
        page: str = driver.page_source
        driver.close()
        return page

    @staticmethod
    def __get_product_name(soup: BeautifulSoup) -> Optional[str]:
        """Return the porduct name."""

        name = soup.find(class_="js-product__title xf-product-card__title")
        if name:
            name = name.text.split("\n")[0]
        return name

    @staticmethod
    def __raise_error(function_name: str) -> NoReturn:
        """Raise error if status code not equal 200."""

        raise ValueError(f"Проблема с подключением к сети в функции {function_name}.")

    def get_catalog(self) -> Set[Category]:
        """Return set of namedtuples about all categories in the catalog."""

        result: Set[Category] = set()
        resp = req.get(self.url_catalog)
        if resp.status_code != 200:
            self.__raise_error(self.get_catalog.__name__)
        soup = BeautifulSoup(resp.text, "lxml")
        for cat in soup.find_all(class_="xf-catalog-categories__item"):
            href = cat.find(class_="xf-catalog-categories__link").get("href")
            name = cat.text.strip()
            result.add(Category(name, self.main_url + href))

        return result

    def __parse_good(self, url: str) -> Dict[str, Optional[str]]:
        """Parse information about the product."""

        product: Dict[str, Optional[str]] = {}
        _ = [product.setdefault(key, None) for key in self.columns]
        resp = req.get(url)
        if resp.status_code != 200:
            self.__raise_error(self.__parse_good.__name__)
        soup = BeautifulSoup(resp.text, "lxml")
        product["Название"] = self.__get_product_name(soup)
        table = soup.find(
            "table", attrs={"class": "xf-product-info__table xf-product-table"}
        )
        if table:
            rows = table.find_all("tr")
            for row in rows:
                key = row.find_all(class_="xf-product-table__col-header")[
                    0
                ].text.strip()
                value = row.find_all("td")[0].text.strip()
                if key == "Объём":
                    key = "Вес"
                if key in self.columns:
                    product[key] = value
        return product

    def __parse_category(self, category: Category) -> pd.DataFrame:
        """Parse all products in the categoty."""

        print(f"Start parsing {category.name}.")
        page = self.__get_html(category.url)
        soup = BeautifulSoup(page, "lxml")
        goods = soup.find_all(class_="js-catalog-product _additionals xf-catalog__item")
        for good in goods:
            url = good.find(class_="xf-product-picture__link js-product__image").get(
                "href"
            )
            url = self.main_url + url
            product = self.__parse_good(url)
            product["Категория"] = category.name
            self.result = pd.concat(
                [self.result, pd.DataFrame.from_dict(product, orient="index").T]
            )

        self.result = self.result.dropna(subset=["Название"]).drop_duplicates(
            subset=["Название"]
        )
        return self.result

    def parse(self) -> pd.DataFrame:
        """Parse all products descriptions from `https://www.perekrestok.ru`."""

        for category in self.get_catalog():
            self.__parse_category(category)
        return self.result


if __name__ == "__main__":
    parser = Perecrestok()
    data = parser.parse()
    data.to_csv("perecrestok_goods.csv")
