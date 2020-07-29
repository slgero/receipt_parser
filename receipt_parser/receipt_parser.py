"""
Provide various types of technologies for recognition
and normalization product descriptions.
"""
import os
from typing import Union, Optional, Dict
import wget  # type: ignore
import pandas as pd  # type: ignore

try:
    from receipt_parser.finder import Finder  # type: ignore
    from receipt_parser.normalizer import Normalizer  # type: ignore
except ImportError:
    from finder import Finder  # type: ignore
    from normalizer import Normalizer  # type: ignore


class DownloadData:
    """Download some data that i can't add to PyPi."""

    def __init__(self):
        # pylint: disable=line-too-long
        self.base_url = "https://raw.githubusercontent.com/slgero/receipt_parser/master/receipt_parser"
        self.files: Dict[str, str] = {
            "cleaned/all_clean.csv": f"{self.base_url}/data/cleaned/all_clean.csv",
            "cleaned/brands_en.csv": f"{self.base_url}/data/cleaned/brands_en.csv",
            "cleaned/brands_ru.csv": f"{self.base_url}/data/cleaned/brands_ru.csv",
            "cleaned/products.csv": f"{self.base_url}/data/cleaned/products.csv",
            "blacklist.csv": f"{self.base_url}/data/blacklist.csv",
            "cat_bpe_model.yttm": f"{self.base_url}/models/cat_bpe_model.yttm",
            "cat_model.pth": f"{self.base_url}/models/cat_model.pth",
        }
        self.home_folder: str = os.path.join(os.getcwd(), "data")

    @staticmethod
    def _is_folder_exists() -> bool:
        """Check if folder `data` exists."""

        pwd: str = os.getcwd()
        data_folder: str = os.path.join(pwd, "data")
        return os.path.isdir(data_folder)

    @staticmethod
    def _make_dirs() -> None:
        """Make 3 dirs: `data/`, `models` and `data/cleaned`."""

        os.makedirs("data")
        os.makedirs(os.path.join("data", "cleaned"))
        os.makedirs(os.path.join("data", "models"))

    def download_files(self) -> None:
        """Download files from my github account."""

        for name, url in self.files.items():
            print(f"Download {name.split('/')[-1]}")
            wget.download(url, os.path.join("data", name))

    def get_pathes(self) -> Dict[str, str]:
        """Return new pathes to files."""

        pathes: Dict[str, str] = {}

        for path in self.files:
            name = path.split("/")[-1].split(".")[0]
            pathes[name] = os.path.join(self.home_folder, path)
        return pathes

    def download(self) -> Dict[str, str]:
        """Download files and return new pathes."""

        if not self._is_folder_exists():
            print("It's need to download some data...")
            self._make_dirs()
            self.download_files()
        return self.get_pathes()


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
        download_pathes: Dict[str, str] = DownloadData().download()
        pathes = pathes or download_pathes

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
        data = data.drop("name_norm", axis=1)
        return data
