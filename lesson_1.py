import time
import json
from pathlib import Path
import requests


class StatusCodeError(Exception):
    def __init__(self, txt):
        self.txt = txt


class Parser5ka:
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0"
    }

    def __init__(self, start_url):
        self.start_url = start_url

    def _get_response(self, url, **kwargs):
        while True:
            try:
                response = requests.get(url, **kwargs)
                if response.status_code != 200:
                    raise StatusCodeError(f'status {response.status_code}')
                return response
            except (requests.exceptions.ConnectTimeout,
                   StatusCodeError):
                time.sleep(0.1)

    def run(self):
        for products in self.parse(self.start_url):
            for product in products:
                file_path = Path(__file__).parent.joinpath(f'{product["id"]}.json')
                self.save_file(file_path, product)

    def parse(self, url):
        while url:
            response = self._get_response(url, headers=self.headers)
            data = response.json()
            url = data['next']
            yield data.get('results', [])

    def save_file(self, file_path: Path, data: dict):
        with open(file_path, 'w', encoding='UTF-8') as file:
            json.dump(data, file, ensure_ascii=False)


class ParserCatalog(Parser5ka):
    def __init__(self, start_url, category_url):
        self.category_url = category_url
        super().__init__(start_url)

    def get_categories(self, url):
        response = requests.get(url, headers=self.headers)
        return response.json()

    def run(self):
        for category in self.get_categories(self.category_url):
            data = {
                "parent_group_code": category['parent_group_code'],
                "parent_group_name": category['parent_group_name'],
                "products": [],
            }

            for products in self.parse(self.start_url):
                data["products"].extend(products)

            file_path = Path(__file__).parent.joinpath(f'{category["parent_group_code"]}.json')
            self.save_file(file_path, data)


if __name__ == '__main__':
    parser = ParserCatalog('https://5ka.ru/api/v2/special_offers/', 'https://5ka.ru/api/v2/categories/')
    parser.run()

