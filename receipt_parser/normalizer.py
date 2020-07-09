"""Normalize product description"""
import re
from typing import Optional, Union
import pandas as pd  # type: ignore
from data.dicts import PRODUCTS, BRANDS, SLASH_PRODUCTS, BRANDS_WITH_NUMBERS  # type: ignore


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
    data : Union[pd.Series, str]
        Text column with a description of the products to normalize.

    Attributes
    ----------
    df: pd.DataFrame
        Text products description to normalize.
    blacklist: np.ndarray
        Stop word list.
    brands: np.ndarray
        List with  most common English brands.

    Examples
    --------
    >>> product = 'Майонез MR.RICCO Провансаль 67% д/п 400'
    >>> norm = Normalizer(product)
    >>> norm.normalize()
    """

    def __init__(self, data: Union[pd.Series, str]):
        columns = ["name", "name_norm", "product_norm", "brand_norm"]
        if isinstance(data, pd.Series):
            self.data = pd.DataFrame(data, columns=columns)
        else:
            self.data = pd.DataFrame([[data, None, None, None]], columns=columns)

        self.blacklist = pd.read_csv("data/blacklist.csv")["name"].values
        self.brands = pd.read_csv("data/cleaned/brands_en.csv")["brand"].values

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

        eng_brands = "".join(re.findall(r"\b([a-z]+)\b", name))
        name = re.sub(r"\b([a-z]+)\b", "", name)

        if eng_brands and not brand:
            return pd.Series([name, eng_brands])
        return pd.Series([name, brand])

    def normalize(self) -> pd.DataFrame:
        """
        Normalize the description of the product: expand abbreviations,
        delete garbage words and characters for further recognition,
        remove english worlds, etc.
        """

        self.data["name_norm"] = self.data["name"].str.lower()
        self.data[["name_norm", "brand_norm"]] = self.data["name_norm"].apply(
            self._remove_numbers
        )
        self.data[["name_norm", "product_norm", "brand_norm"]] = self.data.apply(
            lambda x: self._remove_punctuation(x["name_norm"], x["brand_norm"]), axis=1
        )
        self.data["name_norm"] = self.data["name_norm"].apply(
            self._remove_one_and_two_chars
        )
        self.data[["name_norm", "brand_norm"]] = self.data.apply(
            lambda x: self.find_en_brands(x["name_norm"], x["brand_norm"]), axis=1
        )
        self.data["name_norm"] = self.data["name_norm"].apply(
            self._remove_words_in_blacklist
        )
        self.data["name_norm"] = self.data["name_norm"].apply(
            self._replace_with_product_dict
        )
        self.data[["name_norm", "brand_norm"]] = self.data.apply(
            lambda x: self._remove_all_english_words(x["name_norm"], x["brand_norm"]),
            axis=1,
        )
        return self.data