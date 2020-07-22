"""Parse info about Peterochka supremarket: `http://pyaterochkaakcii.ru/`."""
import re
from typing import List, Optional, NoReturn
import requests as req
from bs4 import BeautifulSoup  # type: ignore
import pandas as pd  # type: ignore


class ParseProductName:
    """Find brand, product and weight if products desription."""

    def __init__(self, products: pd.DataFrame):
        self.products = products.dropna().drop_duplicates()

    @staticmethod
    def find_brand(name: str) -> Optional[str]:
        """Find brand in product name."""

        pattern = r'"(.*)"'
        brand = re.findall(pattern, name)
        return brand[0] if brand else None

    @staticmethod
    def remove_brand(name: str, brand: str) -> str:
        """Remove brand from product name."""

        return name.replace(f'"{brand}"', "")

    @staticmethod
    def find_weight_or_volume(name: str) -> Optional[str]:
        """Find weight or volume in product name."""

        pattern = r"\d+((\.|\,|x|X|х|Х)?)\d* ?([а-я]|[А-Я])*$"
        result = re.search(pattern, name)
        return result.group(0) if result else None

    @staticmethod
    def find_product(name: str) -> str:
        """Find main product."""

        return name[: name.find(' "')]

    def run_parse(self) -> pd.DataFrame:
        """Find brand, product and weight of goods."""

        self.products["Бренд"] = self.products["Название"].apply(self.find_brand)
        self.products = self.products.dropna()
        self.products["Вес"] = self.products["Название"].apply(
            self.find_weight_or_volume
        )
        self.products["Продукт"] = self.products["Название"].apply(self.find_product)
        return self.products


class Peterochka:
    """Allow to parse all data about products from the Peterochka."""

    def __init__(self):
        self.katalog = {
            "bakaleya": "Соусы, орехи, консервы.",
            "bytovaya-himiya": "Бытовая химия.",
            "zamorozhennye-produkty": "Замороженные продукты.",
            "kolbasa-kopchennosti-myasnye-delikatesy": "Птица, мясо, деликатесы.",
            "konditerskie-izdeliya": "Хлеб, сладости, снеки.",
            "chay-kofe-kakao": "Чай, кофе, сахар.",
            "hlebobulochnye-izdeliya": "Хлеб, сладости, снеки.",
            "tovary-dlya-zhivotnyh": "Зоотовары.",
            "tovary-dlya-detey": "Товары для мам и детей.",
            "specialnoe-pitanie": "Скидки месяца.",
            "sladosti-i-konfety": "Хлеб, сладости, снеки.",
            "ryba-i-moreprodukty": "Рыба, икра.",
            "napitki-soki-vody": "Воды, соки, напитки.",
            "myaso-i-ptica": "Птица, мясо, деликатесы.",
            "kosmetika-i-lichnaya-gigiena": "Красота, гигиена, бытовая химия.",
        }
        self.url = "http://pyaterochkaakcii.ru/katalog/{category}?page={page}"
        self.pages = 20

    @staticmethod
    def __raise_error(function_name: str) -> NoReturn:
        """Raise error if status code not equal 200."""

        raise ValueError(f"Проблема с подключением к сети в функции {function_name}.")

    def parse_category(self, category: tuple) -> List[str]:
        """Parse all products in the categoty."""

        goods = []
        for page in range(self.pages):
            resp = req.get(self.url.format(category=category[0], page=page))
            if resp.status_code != 200:
                self.__raise_error(self.parse_category.__name__)
            soup = BeautifulSoup(resp.text, "lxml")
            names = soup.find_all(class_="name")
            if not names:  # it was the last page
                break
            for name in names:
                goods.append(name.text)
        return goods

    def _parse_all(self) -> pd.DataFrame:
        """Parse all product in `http://pyaterochkaakcii.ru/`."""

        result = pd.DataFrame(columns=["Название", "Категория"])
        for category in self.katalog.items():
            print(f"Start parsing {category[1]}")
            goods = self.parse_category(category)
            tmp = pd.DataFrame(goods, columns=["Название"])
            tmp["Категория"] = category[1]
            result = pd.concat([result, tmp])
        return result

    def parse(self) -> pd.DataFrame:
        """
        Parse all product in `http://pyaterochkaakcii.ru/`
        and transform data with `ParseProductName` class.
        """

        parse_data: pd.DataFrame = self._parse_all()
        product_parser = ParseProductName(parse_data)
        clean_data: pd.DataFrame = product_parser.run_parse()
        return clean_data


if __name__ == "__main__":
    parser = Peterochka()
    data = parser.parse()
    data.to_csv("peterochka_goods.csv")
