import json
import scrapy
import datetime as dt


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com', 'instagram.com', 'i.instagram.com']
    start_urls = ['https://www.instagram.com/accounts/login/']
    _login_path = "/accounts/login/ajax/"
    _tags_path = "/explore/tags/{tag}/"
    api_page_url = "https://i.instagram.com/api/v1/tags/{tag}/sections/"

    def __init__(self, login, password, tags, *args, **kwargs):
        super(InstagramSpider, self).__init__(*args, **kwargs)
        self.login = login
        self.password = password
        self.tags = tags
        self.xcsrf_token = ''
        self.x_instagram_AJAX = ''
        self.x_ig_app_id = '936619743392459'

    def parse(self, response):
        try:
            js_data = self.js_data_extract(response)  # достаем X-CSRFToken
            yield scrapy.FormRequest(
                response.urljoin(self._login_path),
                method="POST",
                callback=self.parse,
                formdata={
                    "username": self.login,  # имена ключей копируем из браузера, из запроса
                    "enc_password": self.password,
                },
                headers={
                    "X-CSRFToken": js_data["config"]["csrf_token"],
                }
            )
        except AttributeError:
            r_data = response.json()  # получаем в ответ json со статусом
            if r_data.get("authenticated"):  # если аутентификация прошла успешно,
                # то открываем страницы с интересующими хэш тегами
                for tag in self.tags:
                    url = self._tags_path.format(tag=tag)
                    yield response.follow(
                        url,
                        callback=self.tag_page_parse,
                    )

    def tag_page_parse(self, response):
        js_data = self.js_data_extract(response)
        self.xcsrf_token = js_data["config"]["csrf_token"]
        self.x_instagram_AJAX = js_data["rollout_hash"]

        # достаем информацию о хэш теге
        tag_data = js_data["entry_data"]["TagPage"][0]['data']
        yield self._get_tag_item(tag_data)
        # достаем информацию о посте
        yield from self._get_post_item(tag_data['recent']['sections'])

        # переходим на вторую страницу
        tag = js_data['entry_data']['TagPage'][0]['data']['name']
        url = self.api_page_url.format(tag=tag)
        yield scrapy.FormRequest(
            url,
            method="POST",
            callback=self.post_parse,
            formdata=self._get_form_data(tag_data["recent"]),
            headers=self._get_headers(),
        )

    def post_parse(self, response):
        r_data = response.json()
        # обработка контента страницы
        if r_data['more_available']:
            yield from self._get_post_item(r_data['sections'])
            # переходим на следующую страницу
            url = response.url
            yield scrapy.FormRequest(
                url,
                callback=self.post_parse,
                formdata= self._get_form_data(r_data),
                headers=self._get_headers(),
            )

    # достаем полезную информацию, которую загрузил инстаграмм на страницу
    def js_data_extract(self, response):
        js = response.xpath("//script[contains(text(), 'window._sharedData = ')]/text()").extract_first()
        start_idx = js.index('{')
        data = json.loads(js[start_idx:-1])
        return data

    # достаем информацию о теге
    def _get_tag_item(self, selector) -> dict():
        tag_item = dict()
        tag_item["item_type"] = "tag"
        tag_item["date_parse"] = dt.datetime.utcnow()
        data = {}
        for key, value in selector.items():
            if not (isinstance(value, dict) or isinstance(value, list)):
                data[key] = value
        tag_item["data"] = data
        return tag_item

    # достаем информацию о посте
    def _get_post_item(self, selector) -> dict():
        for section in selector:
            for media in section['layout_content']['medias']:
                data = media['media']
                post_item = dict()
                post_item["data"] = data
                post_item["item_type"] = "post"
                post_item["date_parse"] = dt.datetime.utcnow()
                yield post_item

    # формируем headers для запроса
    def _get_headers(self) -> dict():
        headers = {
            "X-CSRFToken": self.xcsrf_token,
            "X-Instagram-AJAX": self.x_instagram_AJAX,
            "X-IG-App-ID": self.x_ig_app_id,
        }
        return headers

    # формируем параметры для POST запроса
    def _get_form_data(self, data) ->dict():
        form_data = {
           "include_persistent": "0",
           "max_id": data["next_max_id"],
           "next_media_ids[]": [str(x) for x in data["next_media_ids"]],
           "page": str(data["next_page"]),
           "surface": "grid",
           "tab": "recent",
       }
        return form_data
