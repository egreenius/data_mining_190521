import scrapy
from .loaders import AvitoRealEstateLoader


class AvitoRealEstateSpider(scrapy.Spider):
    name = 'avito'
    allowed_domains = ['www.avito.ru']
    start_urls = ['https://www.avito.ru/moskva/nedvizhimost']

    def parse(self, response):
        yield response.follow(
            response.xpath("//a[@data-category-id='24'][@title='Все квартиры']/@href").get(),
            callback=self.apartment_parse
        )

    def apartment_parse(self, response, paginate=True):
        for url in response.xpath("//div[@data-marker='catalog-serp']//a[@data-marker='item-title']/@href"):
            yield response.follow(url, callback=self.advert_parse)

        for page in range(2, 101) if paginate else []:
            yield response.follow(
                f'?p={page}',
                callback=self.apartment_parse,
                cb_kwargs={'paginate': False}
            )

    def advert_parse(self, response):
        advert_data = {
            "title": {"xpath": "//h1[@class='title-info-title']/span/text()"},
            "price": {"xpath": "//span[@itemprop='price']/@content"},
            "address": {"xpath": "//span[@class='item-address__string']/text()"},
            "parameters": {"xpath": "//ul[@class='item-params-list']/li"},
            "author_url": {"xpath": "//div[@data-marker='seller-info/name']/a/@href"},
        }
        loader = AvitoRealEstateLoader(response=response)
        for key, selector in advert_data.items():
            loader.add_xpath(key, **selector)
        yield loader.load_item()

