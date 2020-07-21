"""
Provide various types of technologies for recognition
and normalization product descriptions.
"""
from typing import Union, Optional, Dict
import pandas as pd  # type: ignore
from finder import Finder
from normalizer import Normalizer


# pylint: disable=too-few-public-methods
class RuleBased:
    """
    Use rules based on regular expressions and
    keyword selective tools on marked datasets to
    recognize product descriptions.

    Parameters
    ----------
    pathes: Optional[Dict[str, str]] (default=None)
        Dictionary with paths to *.csv files.

    Attributes
    ----------
    norm: Normalizer
        Normalize product description: expand abbreviations,
        delete garbage words and characters for further recognition,
        remove english worlds, etc.
    find : Finder
        Search and recognize the name, category and brand of a product
        from its description.

    Examples
    --------
    >>> rules = RuleBased()
    >>> rules.parse(df['name'])
    """

    def __init__(self, pathes: Optional[Dict[str, str]] = None):
        pathes = pathes or {}

        self.norm = Normalizer(pathes)
        self.find = Finder(pathes)

    @staticmethod
    def __transform_data(data: Union[pd.DataFrame, pd.Series, str]) -> pd.Series:
        """Transform data to pd.Series into the desired format."""

        if isinstance(data, pd.DataFrame):
            if "name" not in data.columns:
                raise ValueError(
                    "Столбец с описанием товара должен иметь название `name`."
                )
            return data["name"]
        return pd.Series(data, name="name")

    # pylint: disable=bad-continuation
    def parse(
        self, data: Union[pd.DataFrame, pd.Series, str], verbose: int = 0
    ) -> pd.DataFrame:
        """
        Start the parsing process.

        Parameters
        ----------
        data : Union[pd.DataFrame, pd.Series, str]
            Text column with a description of the products to parse.
        verbose: int (default=0)
            Set verbose to any positive number for verbosity.

        Returns
        -------
        pd.DataFrame
            Recognized product names, brands and product categories.
        """

        data = self.__transform_data(data)
        data = self.norm.normalize(data)
        data = self.find.find_all(data, verbose)
        return data
