import typing
import time
import requests
from urllib.parse import urljoin
import bs4
import pymongo
from datetime import datetime


class GbBlogParse:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/90.0.4430.212 Safari/537.36"
    }
    __parse_time = 0

    def __init__(self, start_url, comments_url, db, delay=1.0):
        self.start_url = start_url
        self.comments_url = comments_url
        self.db = db
        self.delay = delay
        self.done_urls = set()
        self.tasks = []
        self.tasks_creator({self.start_url, }, self.parse_feed)

    def _get_response(self, url, params={}):
        while True:
            next_time = self.__parse_time + self.delay
            if next_time > time.time():
                time.sleep(next_time - time.time())
            if params:
                response = requests.get(url, headers=self.headers, params=params)
            else:
                response = requests.get(url, headers=self.headers)
            print(f"RESPONSE: {response.url}")
            self.__parse_time = time.time()
            if (response.status_code == 200) or (response.status_code ==206):
                return response

    def get_task(self, url: str, callback: typing.Callable) -> typing.Callable:
        def task():
            response = self._get_response(url)
            return callback(response)

        return task

    def tasks_creator(self, urls: set, callback: typing.Callable):
        urls_set = urls - self.done_urls
        for url in urls_set:
            self.tasks.append(
                self.get_task(url, callback)
            )
            self.done_urls.add(url)

    def run(self):
        while True:
            try:
                task = self.tasks.pop(0)
                task()
            except IndexError:
                break

    def parse_feed(self, response: requests.Response):
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        ul_pagination = soup.find('ul', attrs={"class": "gb__pagination"})
        pagination_links = set(
            urljoin(response.url, itm.attrs.get('href'))
            for itm in ul_pagination.find_all('a') if
            itm.attrs.get("href")
        )
        self.tasks_creator(pagination_links, self.parse_feed)
        post_wrapper = soup.find("div", attrs={"class": "post-items-wrapper"})
        self.tasks_creator(
            set(
                urljoin(response.url, itm.attrs.get('href'))
                for itm in post_wrapper.find_all("a", attrs={"class": "post-item__title"}) if
                itm.attrs.get("href")
            ),
            self.parse_post
        )

    def _get_comments(self, url, params) -> list:
        response = self._get_response(url, params=params)
        data: dict = response.json()
        comment = {
            'author': str,
            'text': str
        }
        comments = []
        for item in data:
            comment['text'] = item['comment']['body']
            comment['author'] = item['comment']['user']['full_name']
            comments.append(comment)
        return comments

    def parse_post(self, response: requests.Response):
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        author_name_tag = soup.find('div', attrs={"itemprop": "author"})
        first_image_tag = soup.find('div', attrs={'class': "blogpost-content"}).find('img')
        publish_date_tag = soup.find('div', attrs={"class": "blogpost-date-views"}).find('time')
        publish_date = datetime.strptime(publish_date_tag['datetime'], '%Y-%m-%dT%H:%M:%S%z')
        comments_attrs = soup.find('div', attrs={'class': 'm-t-xl'}).find('comments')
        comments_params = {
            'commentable_type': comments_attrs['commentable-type'],
            'commentable_id': comments_attrs['commentable-id'],
            'order': comments_attrs['order']
        }
        comments = self._get_comments(self.comments_url, comments_params)
        data = {
            'url': response.url,
            "title": soup.find('h1', attrs={'class': "blogpost-title"}).text,
            "first_image": first_image_tag['src'] if first_image_tag is not None else 'None',
            "publish_date": publish_date,
            "comments": comments,
            "author": {
                'url': urljoin(response.url, author_name_tag.parent.attrs["href"]),
                'name': author_name_tag.text
            }
        }
        self._save(data)

    def _save(self, data: dict):
        collection = self.db["hw_gb_blog_parse"]
        collection.insert_one(data)


if __name__ == '__main__':
    client_db = pymongo.MongoClient("mongodb://localhost:27017")
    db = client_db["gb_parse_18_05"]
    blogs_url = "https://gb.ru/posts"
    comments_url = "https://gb.ru/api/v2/comments"
    parser = GbBlogParse(blogs_url, comments_url, db)
    parser.run()
    print("Программа завершила свою работу")