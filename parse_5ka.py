#from os import path
import json
from pathlib import Path
import time
import requests

# url = "https://5ka.ru/api/v2/special_offers/"
#
# params = {
#     "store": "363H"
# }
# headers = {
#     "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) "
#                   "Version/14.0 Safari/605.1.15"
# }
# response = requests.get(url, params=params, headers=headers)
#
# # Path(__file__) - путь к файлу где переменная была вызвана
# # .parent - директория пути выше
# # .joinpath - аргументом берет имя файла и присоединяет к папке, класса, членом которого он является
# tmp_file = Path(__file__).parent.joinpath("tmp.htm")
#
# # tmp_file.write_bytes(response.content)
# data = response.json()
# print(1)

class Parse5ka:
    headers = {
        "User-Agent": "Alla Pugacheva"
    }

    def __init__(self, start_url, save_path:Path):
        self.start_url = start_url
        self.save_path = save_path

    def _get_response(self, url):
        while True:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response
            time.sleep(0.5)

    def run(self):
        for product in self._parse(self.start_url):
            file_path = self.save_path.joinpath(f"{product['id']}.json")
            self._save(product, file_path)

    def _parse(self, url):
        while url:
            response = self._get_response(url)
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
    url = "https://5ka.ru/api/v2/special_offers/" # https://5ka.ru/api/v2/categories/
    product_path = get_save_path('products')
    parser = Parse5ka(url, product_path)
    parser.run()
