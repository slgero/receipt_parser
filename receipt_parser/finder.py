"""
Search and recognize the name, category and
brand of a product from its description.
"""
from typing import Optional, List, Union
from itertools import combinations
import pandas as pd  # type: ignore
from pymystem3 import Mystem  # type: ignore

# pylint: disable=C1801


class Finder:
    """
    Search and recognize the name, category and brand of a product
    from its description.
    Search is carried out in the collected datasets: `brands_ru.csv`,
    `products.csv`, `all_clean.csv`.

    Parameters
    ----------
    data_to_parse: Union[pd.DataFrame, str],
        Data in which product information will be recognized.
        If data is a pd.DataFrane, it must contain the following columns:
        ['name_norm', 'product_norm', 'brand_norm'].
        If the data is a string, it should be normalized:
        service characters removed, lowercase letters, etc.

    Attributes
    ----------
    mystem : class
        A Python wrapper of the Yandex Mystem 3.1 morphological
        analyzer (http://api.yandex.ru/mystem).
        See aslo `https://github.com/nlpub/pymystem3`.
    rus_brands : np.ndarray
        List of Russian brands.
    products : pd.DataFrame
        DataFrame of product names and categories.
    df : pd.DataFrame
        The copy of `data_to_parse`.

    Examples
    --------
    >>> product = 'Майонез MR.RICCO Провансаль 67% д/п 400'
    >>> finder = Finder(product)
    >>> finder.find_all()

    Notes
    -----
    You may be comfortable with the following resource:
    'https://receiptnlp.tinkoff.ru/'.
    """

    def __init__(self, data_to_parse: Union[pd.DataFrame, str]):
        self.mystem = Mystem()

        # DataFrames:
        self.rus_brands = pd.read_csv("data/cleaned/brands_ru.csv")["brand"].values
        self.products = pd.read_csv("data/cleaned/products.csv")
        self.product_db = pd.read_csv("data/cleaned/all_clean.csv")

        columns = ["name_norm", "product_norm", "brand_norm"]
        if isinstance(data_to_parse, pd.DataFrame):
            self.data = data_to_parse[columns].copy()
        else:
            self.data = pd.DataFrame([[data_to_parse, None, None]], columns=columns)
        self.data["cat_norm"] = None  # Add new column

    def find_brands(self, name: str, brand: Optional[str] = None) -> pd.Series:
        """
        Find Russian brands using the dataset `brands_ru.csv`.
        For more accurate recognition, a combination of words in a
        different order is used.

        Parameters
        ----------
        name : str
            Product name.
        brand : str, optional (default=None)
            Product category.

        Returns
        -------
        pd.Series
           pd.Series([name, brand])
        """

        if name and not brand:
            names = set(
                [f"{comb[0]} {comb[1]}" for comb in combinations(name.split(), 2)]
                + name.split()
            )
            for rus_brand in self.rus_brands:
                if rus_brand in names:
                    name = name.replace(rus_brand, "").replace("  ", " ").strip()
                    return pd.Series([name, rus_brand])
        return pd.Series([name, brand])

    @staticmethod
    def __remove_duplicate_word(arr: List[str]) -> List[str]:
        """
        Remove duplicates in words when one name is a  continuation
        of another: ['вода', 'вода питьевая'] --> ['вода питьевая'].

        Parameters
        ----------
        arr : List[str]
            List description of products in different variants.

        Returns
        -------
        arr : List[str]
            List description of products without duplicates.
        """

        if max([len(x.split()) for x in arr]) > 1:
            arr = sorted(arr, key=lambda x: len(x.split()))
            one_words = []
            for product in arr.copy():
                if len(product.split()) == 1:
                    one_words.append(product)
                else:
                    for word in one_words:
                        if word in product:
                            arr.remove(word)
        return arr

    # pylint: disable=C0330
    def find_product(
        self, name: str, product: str, category: Optional[str] = None
    ) -> pd.Series:
        """
        Find products name using the dataset `products.csv`.
        For more accurate recognition, a combination of words in a
        different order is used.

        Parameters
        ----------
        name : str
            Product name.
        product : str
            Product description.
        category : str, optional (default=None)
            Product category.

        Returns
        -------
        pd.Series
           pd.Series([name, product, category])
        """

        if name and not product:
            names = pd.DataFrame(
                set(
                    [f"{comb[0]} {comb[1]}" for comb in combinations(name.split(), 2)]
                    + name.split()
                ),
                columns=["product"],
            )
            merge = self.products.merge(names)
            if len(merge):
                product = ", ".join(
                    self.__remove_duplicate_word(merge["product"].values)
                )
                category = merge["category"].value_counts().index[0]
        return pd.Series([name, product, category])

    def _use_mystem(self, name: str, product: str) -> str:
        """
        Use Yandex pymystem3 library to lemmatize words in product descriptions.
        I tried to use pymorphy, but the recognition quality got worse.

        Parameters
        ----------
        name : str
            Product name.
        product : str
            Product description.

        Returns
        -------
        str
            Product description after lemmatization.

        Notes
        -----
        See also `https://github.com/nlpub/pymystem3`.
        """

        if name and not product:
            name = "".join(self.mystem.lemmatize(name)[:-1])
        return name

    def find_category(self, product: str, category: str) -> pd.Series:
        """
        Find a product category using the dataset `products.csv`.

        Parameters
        ----------
        product : str
            Product description.
        category : str
            Product category.

        Returns
        -------
        pd.Series
           pd.Series([product, category])
        """

        if product and not category:
            tmp = self.products[self.products["product"] == product]
            if len(tmp):
                category = tmp["category"].values[0]

        return pd.Series([product, category])

    def find_product_by_brand(
        self, product: str, brand: str, category: str
    ) -> pd.Series:
        """
        If we were able to recognize the product brand,
        but could not recongize the product name,
        we can assign the most common product name for this brand.

        Parameters
        ----------
        product : str
            Product description.
        brand : str
            Product brand.
        category : str
            Product category.

        Returns
        -------
        pd.Series
           pd.Series([product, brand, category])
        """

        if brand and not product:
            single_brand_goods = self.product_db[self.product_db["Бренд"] == brand]
            if len(single_brand_goods):
                product = single_brand_goods["Продукт"].value_counts().index[0]
                category = single_brand_goods["Категория"].value_counts().index[0]

        return pd.Series([product, brand, category])

    def __print_logs(self, message: str, verbose: int) -> None:
        """
        Print the number of recognized brands,
        categories and names of goods.
        """

        if verbose:
            _len = len(self.data)
            print(message)
            print(
                "Recognized brands: "
                f"{len(self.data['brand_norm'].dropna())}/{_len}, "
                f"products: {len(self.data['product_norm'].dropna())}/{_len}, "
                f"categories: {len(self.data['cat_norm'].dropna())}/{_len}",
                "-" * 80,
                sep="\n",
                end="\n\n",
            )

    def find_all(self, *, verbose: int = 0) -> None:
        """
        Start search and recognition in `data_to_parse`.

        Parameters
        ----------
        verbose: int (default=0)
            Set verbose to any positive number for verbosity.
        """

        self.__print_logs("Before:", verbose)

        # Find brands:
        self.data[["name_norm", "brand_norm"]] = self.data.apply(
            lambda x: self.find_brands(x["name_norm"], x["brand_norm"]), axis=1
        )
        self.__print_logs("Find brands:", verbose)

        # Find product and category:
        self.data[["name_norm", "product_norm", "cat_norm"]] = self.data.apply(
            lambda x: self.find_product(x["name_norm"], x["product_norm"]), axis=1
        )
        self.__print_logs("Find product and category:", verbose)

        # Remove `-`:
        self.data["name_norm"] = self.data["name_norm"].str.replace("-", " ")
        self.data[["name_norm", "product_norm", "cat_norm"]] = self.data.apply(
            lambda x: self.find_product(
                x["name_norm"], x["product_norm"], x["cat_norm"]
            ),
            axis=1,
        )
        self.__print_logs(
            "Remove `-` and the second attempt to find a product:", verbose
        )

        # Use Mystem:
        self.data["name_norm"] = self.data.apply(
            lambda x: self._use_mystem(x["name_norm"], x["product_norm"]), axis=1
        )
        self.data[["name_norm", "product_norm", "cat_norm"]] = self.data.apply(
            lambda x: self.find_product(
                x["name_norm"], x["product_norm"], x["cat_norm"]
            ),
            axis=1,
        )
        self.__print_logs(
            "Use Mystem for lemmatization and the third attempt to find a product:",
            verbose,
        )

        # Find category:
        self.data[["product_norm", "cat_norm"]] = self.data.apply(
            lambda x: self.find_category(x["product_norm"], x["cat_norm"]), axis=1
        )
        self.__print_logs("Find the remaining categories:", verbose)

        # Find product by brand:
        self.data[["product_norm", "brand_norm", "cat_norm"]] = self.data.apply(
            lambda x: self.find_product_by_brand(
                x["product_norm"], x["brand_norm"], x["cat_norm"]
            ),
            axis=1,
        )
        self.__print_logs("Find product by brand:", verbose)
        return self.data
