"""Normalize product description."""
import re
from typing import Optional, Union, Dict
import pandas as pd  # type: ignore
from pandarallel import pandarallel  # type: ignore

pandarallel.initialize(progress_bar=False, verbose=0)

try:
    # pylint: disable=line-too-long
    from receipt_parser.dicts import PRODUCTS, BRANDS, SLASH_PRODUCTS, BRANDS_WITH_NUMBERS  # type: ignore
except ModuleNotFoundError:
    from dicts import PRODUCTS, BRANDS, SLASH_PRODUCTS, BRANDS_WITH_NUMBERS  # type: ignore


# pylint: disable=bad-continuation
class Apply:
    """User define the `apply` function from pd.Series and pd.DataFrame"""

    @staticmethod
    def series_apply(data: pd.Series, func, use_parallel: Optional[bool] = None):
        """
        User define the `apply` function from pd.Series.

        Parameters
        ----------
        data : pd.Series
            The data on which the `func` function will be applied.
        func : function
            Function to apply to each column or row.
        use_parallel : Optional[bool], default=None
            Multiprocessing will be used if the data size is greater than 30000.

        Returns
        -------
        pd.DataFrame
            Result of applying ``func`` on the Series.

        Examples
        --------
        >>> from pandas import Series

        >>> Series.my_apply = series_apply
        >>> df['name'].my_apply(foo)
        """

        if use_parallel is None:
            use_parallel = len(data) >= 10000
        if use_parallel:
            return data.parallel_apply(func)
        return data.apply(func)

    @staticmethod
    def df_apply(
        data: pd.DataFrame, func, use_parallel: Optional[bool] = None, axis: int = 1
    ) -> pd.DataFrame:
        """
        User define the `apply` function from pd.DataFrame.
        Use only for 2-column data.

        Parameters
        ----------
        data : pd.DataFrame
            The data on which the `func` function will be applied.
        func : function
            Function to apply to each column or row.
        use_parallel : Optional[bool], default=None
            Multiprocessing will be used if the data size is greater than 30000.
        axis : {0 or 'index', 1 or 'columns'}, default=1
            Axis along which the function is applied.

        Returns
        -------
        pd.DataFrame
            Result of applying ``func`` along the given axis of the DataFrame.

        Examples
        --------
        >>> from pandas import DataFrame

        >>> DataFrame.my_apply = df_apply
        >>> df[['name', 'brand']].my_apply(foo)
        """

        _cols = data.columns

        if use_parallel is None:
            use_parallel = len(data) >= 10000

        if use_parallel:
            return data.parallel_apply(
                lambda x: func(x[_cols[0]], x[_cols[1]]), axis=axis
            )
        return data.apply(lambda x: func(x[_cols[0]], x[_cols[1]]), axis=axis)


class Normalizer:
    """
    Normalize product description: expand abbreviations,
    delete garbage words and characters for further recognition,
    remove english worlds, etc.
    Steps:
    1. Convert to lowercase;
    2. Delete all words including numbers;
    3. Delete all service characters;
    4. Delete words consisting of 1 or 2 characters;
    5. Find English brands using the dataset `brands_en.csv`;
    6. Delete words from blacklist and words in English;
    7. Replace words using `dicts.PRODUCTS`.

    Parameters
    ----------
    pathes: Optional[Dict[str, str]], (default=None)
        Dictionary with paths to *.csv files.

    Attributes
    ----------
    blacklist: np.ndarray
        Stop word list.
    brands: np.ndarray
        List with  most common English brands.

    Examples
    --------
    >>> product = 'Майонез MR.RICCO Провансаль 67% д/п 400'
    >>> norm = Normalizer()
    >>> norm.normalize(product)
    """

    def __init__(self, pathes: Optional[Dict[str, str]] = None):
        pathes = pathes or {}
        self.blacklist = pd.read_csv(pathes.get("blacklist", "data/blacklist.csv"))[
            "name"
        ].values
        self.brands = pd.read_csv(
            pathes.get("brands_en", "data/cleaned/brands_en.csv")
        )["brand"].values

        # Init user define apply function:
        pd.DataFrame.appl = Apply.df_apply
        pd.Series.appl = Apply.series_apply

    @staticmethod
    def _remove_numbers(name: str) -> pd.Series:
        """Remove all words in product description which contain numbers."""

        brand = None
        # Find brands with numbers:
        for key, value in BRANDS_WITH_NUMBERS.items():
            if key in name:
                brand = value
                name = name.replace(key, "")
                break

        name = " ".join(re.sub(r"\w*\d\w*", "", word) for word in name.split())
        return pd.Series([name, brand])

    @staticmethod
    def _remove_punctuation(name: str, brand: Optional[str]) -> pd.Series:
        """Remove all service characters in product description."""

        # Find abbreviations:
        for key, value in BRANDS.items():
            if key in name:
                brand = value
                name = name.replace(key, "")
                break

        product = None
        for key, value in SLASH_PRODUCTS.items():
            if key in name:
                product = value
                name = name.replace(key, " ")
                break

        # Pattern: remove `-` after the sentence and remove almost all service chars
        pattern = r"((?<=\w)-+(?!\w))|([.,+!?%:№*/\(|\)])"
        name = re.sub(pattern, " ", name).replace("  ", " ")
        return pd.Series([name, product, brand])

    def find_en_brands(self, name: str, brand: Optional[str]) -> pd.Series:
        """Find English brands using the dataset `brands_en.csv`."""

        if not brand:
            for brand_en in self.brands:
                if brand_en in name:
                    brand = brand_en
                    name = name.replace(brand_en, "")
                    break

        return pd.Series([name, brand])

    @staticmethod
    def _remove_one_and_two_chars(name: str) -> str:
        """Remove words consisting of 1 or 2 characters."""

        return " ".join(x for x in name.split() if len(x) > 2)

    def _remove_words_in_blacklist(self, name: str) -> str:
        """Remove words from blacklist."""

        return " ".join(word for word in name.split() if word not in self.blacklist)

    @staticmethod
    def _replace_with_product_dict(name: str) -> str:
        """Replace words using `dicts.PRODUCTS`."""

        return " ".join(PRODUCTS.get(word, word) for word in name.split())

    @staticmethod
    def _remove_all_english_words(name: str, brand: Optional[str]) -> pd.Series:
        """
        Remove all English words in the product description.
        We make the assumption that these words are a brand.
        """

        eng_brands = " ".join(re.findall(r"\b([a-z]+)\b", name))
        name = re.sub(r"\b([a-z]+)\b", "", name)

        if eng_brands and not brand:
            return pd.Series([name, eng_brands])
        return pd.Series([name, brand])

    @staticmethod
    def __transform_data(data: Union[pd.Series, str]) -> pd.DataFrame:
        """Transform pd.Series or str to pd.DataFrame."""

        columns = ["name", "name_norm", "product_norm", "brand_norm"]

        if isinstance(data, pd.Series):
            return pd.DataFrame(data, columns=columns)
        return pd.DataFrame([[data, None, None, None]], columns=columns)

    def normalize(self, data: Union[pd.Series, str]) -> pd.DataFrame:
        """
        Normalize the description of the product: expand abbreviations,
        delete garbage words and characters for further recognition,
        remove english worlds, etc.

        Parameters
        ----------
        data : Union[pd.Series, str]
            Text column with a description of the products to normalize.

        Returns
        -------
        pd.DataFrame
            Normalized description dataframe.
        """

        data = self.__transform_data(data)
        data["name_norm"] = data["name"].str.lower()
        data[["name_norm", "brand_norm"]] = data["name_norm"].appl(self._remove_numbers)
        data[["name_norm", "product_norm", "brand_norm"]] = data[
            ["name_norm", "brand_norm"]
        ].appl(self._remove_punctuation)
        data["name_norm"] = data["name_norm"].appl(self._remove_one_and_two_chars)
        data[["name_norm", "brand_norm"]] = data[["name_norm", "brand_norm"]].appl(
            self.find_en_brands
        )
        data["name_norm"] = data["name_norm"].appl(self._remove_words_in_blacklist)
        data["name_norm"] = data["name_norm"].appl(self._replace_with_product_dict)
        data[["name_norm", "brand_norm"]] = data[["name_norm", "brand_norm"]].appl(
            self._remove_all_english_words
        )
        return data
