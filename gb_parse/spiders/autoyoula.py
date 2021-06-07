import scrapy
import re
from gb_parse.items import GbParseItem  # импортируем класс наш класс GbParseItem,
# в котором мы определили структуру класса Item


class AutoyoulaSpider(scrapy.Spider):
    name = 'autoyoula'  # имя нашего паука
    allowed_domains = ['auto.youla.ru']  # домен, в пределах которого должен работать паук
    start_urls = ['https://auto.youla.ru/']  # базовый url, с которого должен начать обработку паук

    # убираем дублирование кода, опредилив функцию для получения ссылок для их последующей передачи в очередь
    # в качестве переметров - селектор и функция, которая должна будет обработать эти ссылки
    def _get_follow(self, response, selector_str, callback):
        for a_link in response.css(selector_str):
            url = a_link.attrib.get("href")
            yield response.follow(url, callback=callback)  # передача ссылок и функции callback управляющему процессу

    def parse(self, response):
        # передача ссылок и функции которая должна их обработать управляющему процессу для конкретного селектора и
        # конкретной функции обработчика для порождения задачи обработки следующей страницы по url
        yield from self._get_follow(
            response,
            ".TransportMainFilters_brandsList__2tIkv a.blackLink",
            self.brand_parse
        )

        # for a_link in response.css(".TransportMainFilters_brandsList__2tIkv a.blackLink"):
        #     url = a_link.attrib.get("href")
        #     yield response.follow(url, callback=self.brand_parse)  # порождение задачи перехода
        #                                             # для следующую страницу по url
        #                                             # callbak - функция, которая должна обработать этот url
        #                                             # а это функция обрабатывающая страницу конкретного бренда

    def brand_parse(self, response):
        # передача ссылок на объявления и функции обработчика на странице конкретного бренда
        # для порождения задач обработки страниц конкретного бренда
        yield from self._get_follow(
            response,
            ".Paginator_block__2XAPy a.Paginator_button__u1e7D",
            self.brand_parse
        )
        #  передача ссылок и функции обработчика конкретных объявлений
        #  для порождения задач обработки конкретных объявлений
        yield from self._get_follow(
            response,
            "a.SerpSnippet_name__3F7Yu.blackLink",
            self.car_parse
        )
        # for a_link in response.css(".Paginator_block__2XAPy a.Paginator_button__u1e7D"):
        #     url = a_link.attrib.get("href")
        #     yield response.follow(url, callback=self.brand_parse)

    def get_author_id(self, resp):
        marker = "window.transitState = decodeURIComponent"
        for script in resp.css("script"):
            try:
                if marker in script.css("::text").extract_first():
                    re_pattern_user = re.compile(r"youlaId%22%2C%22([a-zA-Z|\d]+)%22%2C%22avatar")
                    re_pattern_dealer = re.compile(r"cardealers%2F([a-zA-Z|\d-]+)%2F%23info")
                    result_user = re.findall(re_pattern_user, script.css("::text").extract_first())
                    result_dealer = re.findall(re_pattern_dealer, script.css("::text").extract_first())
                    if result_user:
                        result = resp.urljoin(f"/user/{result_user[0]}").replace("auto.", "", 1)
                    elif result_dealer:
                        result = resp.urljoin(f"/cardealers/{result_dealer[0]}")
                    else:
                        None
                    return result
            except TypeError:
                pass

    def car_parse(self, response):
        # response.css(".AdvertCard_advertTitle__1S1Ak::text").extract_first()
        item = GbParseItem()
        item['title'] = response.css(".AdvertCard_advertTitle__1S1Ak::text").extract_first()
        item['url'] = response.url
        item['price'] = float(response.css(".AdvertCard_price__3dDCr::text").get().replace("\u2009", ""))
        item['photo'] = [i_img.attrib.get('src') for i_img in response.css("figure.PhotoGallery_photo__36e_r img")]
        item['features'] = [
            {
                'name': i_spec.css('.AdvertSpecs_label__2JHnS::text').get(),
                'value': i_spec.css('.AdvertSpecs_data__xK2Qx a::text').get()
                if i_spec.css('.AdvertSpecs_data__xK2Qx a::text').get()
                else i_spec.css('.AdvertSpecs_data__xK2Qx::text').get()

            }
            for i_spec in response.css(".AdvertCard_specs__2FEHc .AdvertSpecs_row__ljPcX")
        ]
        item['description'] = response.css(".AdvertCard_descriptionInner__KnuRi::text").extract_first()
        item['author'] = self.get_author_id(response)
        yield item  # передача объекта Item управляющему процессу для передачи в заданные Pipelines
