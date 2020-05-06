"""Use Tinkoff(`https://receiptnlp.tinkoff.ru/`) to parse product goods."""
import sys
from time import sleep
from typing import List
from multiprocessing import Pool
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


class Tinkoff:
    """Use Tinkoff server to parse product goods. Use Chrome browser."""

    def __init__(self):
        self.url = 'https://receiptnlp.tinkoff.ru/'

    def get_session(self) -> None:
        """Open browser."""

        self.driver = webdriver.Chrome()
        self.driver.get(self.url)

    def fil_fields(self, name: str) -> None:
        """Delete last text in the field and add new one."""

        window = self.driver.find_element_by_class_name('_3gY2s')
        window.send_keys(Keys.CONTROL + "a")
        window.send_keys(Keys.DELETE)
        window.send_keys(name)
        button = self.driver.find_element_by_xpath("//button[@type='submit']")
        button.click()
        sleep(0.5)

    def parse_table(self) -> dict:
        """Parse information on the check."""

        table = self.driver.find_element_by_class_name("Mnf-LQLHUyIQdT1VvKhCE")
        result = {}
        for row in table.text.split('\n'):
            result[row.split()[0]] = ' '.join(row.split()[1:])
        return result

    def parse_data(self, products: List[str]) -> List[dict]:
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

    df = pd.read_csv(path)
    target_column = 'Название'
    if target_column not in df.columns:
        raise KeyError('Столбец с продкутами должен иметь название "Название"')
    df = df['Название'].apply(lambda x: [x]).values[:9].tolist()
    return get_batches(df, processes_count)


def transform_and_save(data: List[List[dict]], path_to_save: str) -> None:
    """Expand list if lists and save as csv file."""

    data = [item for elem in data for item in elem]  # List[List[dict]] -> List[dict]
    pd.DataFrame.from_dict(data).to_csv(path_to_save, index=False)


if __name__ == '__main__':
    _, path_to_db, path_to_save, processes_count = sys.argv
    processes_count = int(processes_count)
    data = prepare_data_to_parse(path_to_db, processes_count)
    tinkoff = Tinkoff()
    pool = Pool(processes_count)
    result = pool.map(tinkoff.parse_data, data)
    transform_and_save(result, path_to_save)
    p.close()
