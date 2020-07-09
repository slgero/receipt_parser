"""Use Tinkoff(`https://receiptnlp.tinkoff.ru/`) to parse product goods."""
import sys
from time import sleep
from typing import List, Dict
from multiprocessing import Pool
import pandas as pd  # type: ignore
from selenium import webdriver  # type: ignore
from selenium.webdriver.common.keys import Keys  # type: ignore
# pylint: disable=unbalanced-tuple-unpacking


class Tinkoff:
    """Use Tinkoff server to parse product goods. Use Chrome browser."""

    def __init__(self):
        self.url = "https://receiptnlp.tinkoff.ru/"
        self.driver = None

    def get_session(self) -> None:
        """Open browser."""

        self.driver = webdriver.Chrome()
        self.driver.get(self.url)

    def fil_fields(self, name: str) -> None:
        """Delete last text in the field and add new one."""

        window = self.driver.find_element_by_class_name("_3gY2s")
        window.send_keys(Keys.CONTROL + "a")
        window.send_keys(Keys.DELETE)
        window.send_keys(name)
        button = self.driver.find_element_by_xpath("//button[@type='submit']")
        button.click()
        sleep(0.5)

    def parse_table(self) -> Dict[str, str]:
        """Parse information on the check."""

        table = self.driver.find_element_by_class_name("Mnf-LQLHUyIQdT1VvKhCE")
        result = {}
        for row in table.text.split("\n"):
            result[row.split()[0]] = " ".join(row.split()[1:])
        return result

    def parse_data(self, products: List[str]) -> List[Dict[str, str]]:
        """Start parsing data."""

        self.get_session()
        result = []
        for name in products:
            self.fil_fields(name)
            result.append(self.parse_table())
        self.driver.close()
        return result


def get_batches(products: List[str], processes_count: int) -> List[List[str]]:
    """Split List to List[List] for using the multiprocessing."""

    result = []
    bath_size = round(len(products) / processes_count)
    for i in range(0, len(products), bath_size):
        result.append(products[i: i + bath_size])
    return result


def prepare_data_to_parse(path: str, processes_count: int) -> List[List[str]]:
    """Read data and prepare it to use in a multiprocessing."""

    data = pd.read_csv(path)
    target_column = "Название"
    if target_column not in data.columns:
        raise KeyError('Dataset must have a column with name "Название"')
    data = data["Название"].apply(lambda x: [x]).values.tolist()
    return get_batches(data, processes_count)


def transform_and_save(data: List[List[Dict[str, str]]], path_to_save: str) -> None:
    """Expand list if lists and save as csv file."""

    # Expand list: List[List[dict]] -> List[dict]
    data = [item for elem in data for item in elem]  # type: ignore
    pd.DataFrame.from_dict(data).to_csv(path_to_save, index=False)


if __name__ == "__main__":
    _, PATH_TO_DB, PATH_TO_SAVE, PROCESSES_COUNT = sys.argv
    prepared_data = prepare_data_to_parse(PATH_TO_DB, int(PROCESSES_COUNT))
    tinkoff = Tinkoff()
    pool = Pool(int(PROCESSES_COUNT))
    res = pool.map(tinkoff.parse_data, prepared_data)
    transform_and_save(res, PATH_TO_SAVE)
    pool.close()
