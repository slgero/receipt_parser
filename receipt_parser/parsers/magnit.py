"""Parse info about Magnit supremarket in Edadil story: `https://edadeal.ru/`."""
from time import sleep
from typing import List
from selenium import webdriver  # type: ignore


class Magnit:
    """Parse olnly product's names."""

    def __init__(self):
        self.url = 'https://edadeal.ru/moskva/retailers/magnit-univer?page={}'
        self.driver = webdriver.Chrome()
        self.max_pages = 30

    def basic_auth(self) -> None:
        """Prepare the page for parsing."""

        self.driver.get(self.url.format(0))
        sleep(2)
        button = self.driver.find_element_by_class_name('b-rollout__cancel')
        button.click()
        sleep(2)
        self.driver.maximize_window()

    def parse(self) -> List[str]:
        """Parse all product in `https://edadeal.ru`."""

        self.basic_auth()

        names = []
        for page in range(self.max_pages):
            self.driver.get(self.url.format(page))
            sleep(2)
            products = self.driver.find_elements_by_class_name('b-offer__description')
            if len(products) == 0:
                print(f'End on page = {page}.')
                break
            for name in products:
                names.append(name.text)

        return names
    