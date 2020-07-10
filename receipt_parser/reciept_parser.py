from typing import Union
import pandas as pd
from finder import Finder
from normalizer import Normalizer


class RuleBased:
    def __init__(self):
        self.norm = Normalizer()
        self.find = Finder()

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

    def parse(self, data: Union[pd.Series, str]) -> pd.DataFrame:
        data = self.__transform_data(data)
        data = self.norm.normalize(data)
        data = self.find.find_all(data)
        return data
