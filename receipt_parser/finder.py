"""
Search and recognize the name, category and
brand of a product from its description.
"""
from typing import Optional, List, Union, Dict
from itertools import combinations
import pandas as pd  # type: ignore
from pymystem3 import Mystem  # type: ignore

try:
    from cat_model import PredictCategory  # type: ignore
except ImportError:
    from receipt_parser.cat_model import PredictCategory  # type: ignore

# pylint: disable=C1801


def df_apply(data: pd.DataFrame, func, axis: int = 1) -> pd.DataFrame:
    """
        User define the `apply` function from pd.DataFrame.
        Use only for 2-column and 3-column data.

        Parameters
        ----------
        data : pd.DataFrame
            The data on which the `func` function will be applied.
        func : function
            Function to apply to each column or row.
        axis : {0 or 'index', 1 or 'columns'}, default=1
            Axis along which the function is applied.

        Returns
        -------
        pd.DataFrame
            Result of applying ``func`` along the given axis of the
            DataFrame.

        Examples
        --------
        >>> from pandas import DataFrame

        >>> DataFrame.my_apply = df_apply
        >>> df[['name', 'brand']].my_apply(foo)
        """

    _cols = data.columns
    _len = len(_cols)

    if _len == 2:
        return data.apply(lambda x: func(x[_cols[0]], x[_cols[1]]), axis=axis)
    return data.apply(lambda x: func(x[_cols[0]], x[_cols[1]], x[_cols[2]]), axis=axis)


class Finder:
    """
    Search and recognize the name, category and brand of a product
    from its description.
    Search is carried out in the collected datasets: `brands_ru.csv`,
    `products.csv`, `all_clean.csv`.

    Parameters
    ----------
    pathes: Optional[Dict[str, str]], (default=None)
        Dictionary with paths to required files.

    Attributes
    ----------
    mystem : Mystem
        A Python wrapper of the Yandex Mystem 3.1 morphological
        analyzer (http://api.yandex.ru/mystem).
        See aslo `https://github.com/nlpub/pymystem3`.
    cat_model: PredictCategory
        Class for predicting a category by product description
        using a neural network written in PyTorch.
    brands_ru : np.ndarray
        List of Russian brands.
    products : pd.DataFrame
        DataFrame of product names and categories.
    all_clean : pd.DataFrame
        General dataset with all product information.
    data: pd.DataFrame
        Text column with a description of the products to parse.
        Products description should be normalized by Normalizer.
        See `receipt_parser.normalize.Normalizer`.

    Examples
    --------
    >>> product = 'Майонез MR.RICCO Провансаль 67% д/п 400'
    >>> finder = Finder()
    >>> finder.find_all(product)

    Notes
    -----
    You may be comfortable with the following resource:
    'https://receiptnlp.tinkoff.ru/'.
    See also `receipt_parser.parsers.tinkoff`.
    """

    def __init__(self, pathes: Optional[Dict[str, str]] = None):
        pathes = pathes or {}
        self.mystem = Mystem()
        pd.DataFrame.appl = df_apply

        # Init model:
        model_params = {"num_class": 21, "embed_dim": 50, "vocab_size": 500}
        bpe_model = pathes.get("cat_bpe_model", "models/cat_bpe_model.yttm")
        cat_model = pathes.get("cat_model", "models/cat_model.pth")
        self.cat_model = PredictCategory(bpe_model, cat_model, model_params)

        # Read DataFrames:
        brands = pathes.get("brands_ru", "data/cleaned/brands_ru.csv")
        products = pathes.get("products", "data/cleaned/products.csv")
        all_clean = pathes.get("all_clean", "data/cleaned/all_clean.csv")
        self.brands_ru = pd.read_csv(brands)["brand"].values
        self.products = pd.read_csv(products)
        self.all_clean = pd.read_csv(all_clean)
        self.data = pd.DataFrame()

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
            for rus_brand in self.brands_ru:
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
                        if word in product and word in arr:
                            arr.remove(word)
        return arr

    # pylint: disable=bad-continuation
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
                if len(merge) == 1:
                    category = merge["category"].values[0]
                else:
                    category = self.cat_model.predict(name)
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

    def find_category(self, name: str, product: str, category: str) -> pd.Series:
        """
        Find a product category using the dataset `products.csv`.

        Parameters
        ----------
        name : str
            Product name.
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
            else:
                category = self.cat_model.predict(name)

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
            single_brand_goods = self.all_clean[self.all_clean["Бренд"] == brand]
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

    @staticmethod
    def __transform_data(data: Union[pd.DataFrame, str]) -> pd.DataFrame:
        """Transform pd.Series or str to pd.DataFrame."""

        columns = ["product_norm", "brand_norm", "cat_norm"]

        if isinstance(data, str):
            data = pd.DataFrame([data], columns=["name_norm"])
        else:
            if "name_norm" not in data.columns:
                raise ValueError(
                    "Столбец с описанием товара должен иметь название `name_norm`."
                )

        for col in columns:
            if col not in data.columns:
                data[col] = None
        return data

    def __find_all(self, verbose: int) -> None:
        self.__print_logs("Before:", verbose)

        # Find brands:
        self.data[["name_norm", "brand_norm"]] = self.data[
            ["name_norm", "brand_norm"]
        ].appl(self.find_brands)
        self.__print_logs("Find brands:", verbose)

        # Find product and category:
        self.data[["name_norm", "product_norm", "cat_norm"]] = self.data[
            ["name_norm", "product_norm"]
        ].appl(self.find_product)
        self.__print_logs("Find product and category:", verbose)

        # Remove `-`:
        self.data["name_norm"] = self.data["name_norm"].str.replace("-", " ")
        self.data[["name_norm", "product_norm", "cat_norm"]] = self.data[
            ["name_norm", "product_norm", "cat_norm"]
        ].appl(self.find_product)
        self.__print_logs(
            "Remove `-` and the second attempt to find a product:", verbose
        )

        # Use Mystem:
        self.data["name_norm"] = self.data[["name_norm", "product_norm"]].appl(
            self._use_mystem
        )
        self.data[["name_norm", "product_norm", "cat_norm"]] = self.data[
            ["name_norm", "product_norm", "cat_norm"]
        ].appl(self.find_product)
        self.__print_logs(
            "Use Mystem for lemmatization and the third attempt to find a product:",
            verbose,
        )

        # Find category:
        self.data[["product_norm", "cat_norm"]] = self.data[
            ["name_norm", "product_norm", "cat_norm"]
        ].appl(self.find_category)
        self.__print_logs("Find the remaining categories:", verbose)

        # Find product by brand:
        self.data[["product_norm", "brand_norm", "cat_norm"]] = self.data[
            ["name_norm", "product_norm", "cat_norm"]
        ].appl(self.find_product)
        self.__print_logs("Find product by brand:", verbose)

    def find_all(
        self, data: Union[pd.DataFrame, str], verbose: int = 0
    ) -> pd.DataFrame:
        """
        Start search and recognition search processes in `data`.

        Parameters
        ----------
        data : Union[pd.DataFrame, str]
            Text column with a description of the products to parse.
            Products description should be normalized by Normalizer.
            See `receipt_parser.normalize.Normalizer`.
        verbose: int (default=0)
            Set verbose to any positive number for verbosity.

        Returns
        -------
        pd.DataFrame
            Recognized product names, brands and product categories.
        """

        self.data = self.__transform_data(data)
        self.__find_all(verbose)

        return self.data
