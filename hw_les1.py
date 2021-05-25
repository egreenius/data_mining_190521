import json
from pathlib import Path
import time
import requests


class Parse5ka_cat:
    headers = {
        "User-Agent": "Alla Pugacheva"
    }
    params = {
        "categories": ""
    }
    cat_products = {
        "name": str,
        "id": str,
        "products": list
    }

    def __init__(self, start_url, url4cat, save_path: Path):
        self.start_url = start_url
        self.cat_url = url4cat
        self.save_path = save_path

    def _get_response(self, url, params):
        while True:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response
            time.sleep(0.5)

    def run(self):
        for category in self._parse_cat(self.cat_url):
            file_path = self.save_path.joinpath(f"{category['parent_group_code']}.json")
            self.params["categories"] = category['parent_group_code']
            product_list = []
            for product in self._parse(self.start_url, self.params):
                product_list.append(product)
            if product_list:
                self.cat_products["name"] = category['parent_group_name']
                self.cat_products["id"] = category['parent_group_code']
                self.cat_products["products"] = product_list
                self._save(self.cat_products, file_path)

    def _parse_cat(self, url):
        response = self._get_response(url, "")
        data: dict = response.json()
        for cat in data:
            yield cat

    def _parse(self, url, params):
        while url:
            response = self._get_response(url, params)
            data: dict = response.json()
            url = data['next']
            for product in data['results']:
                yield product

    def _save(self, data: dict, file_path: Path):
        file_path.write_text(json.dumps(data, ensure_ascii=False))


def get_save_path(dir_name: str) -> Path:
    save_path = Path(__file__).parent.joinpath(dir_name)
    if not save_path.exists():
        save_path.mkdir()
    return save_path


if __name__ == '__main__':
    url = "https://5ka.ru/api/v2/special_offers/"
    cat_url = "https://5ka.ru/api/v2/categories/"
    product_path = get_save_path('cat_products')
    parser = Parse5ka_cat(url, cat_url, product_path)
    parser.run()
    print("Программа завершила свою работу")
