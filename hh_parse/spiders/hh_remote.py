from copy import copy
from urllib.parse import urlencode
from ..loaders import HhVacancyLoader, HhEmployerLoader

import scrapy


class HhRemoteSpider(scrapy.Spider):
    name = 'hh_remote'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']
    vacancies_api_path = "/shards/employerview/vacancies"
    vacancies_api_list_params = {
        "page": 0,
        "currentEmployerId": None,
        "json": True,
        "regionType": "OTHER",
        "disableBrowserCache": True,
    }

    def _get_follow(self, response, selector_str, callback):
        for a_link in response.xpath(selector_str):
            # url = a_link.extract() # это делать необязательно, scrapy умеет сам извлекать из селекторов
            yield response.follow(a_link, callback=callback)

    def parse(self, response):
        yield from self._get_follow(
            response,
            "//div[@data-qa='pager-block']//a[@class='bloko-button']/@href",
            self.parse
        )
        yield from self._get_follow(
            response,
            "//div[@class= 'vacancy-serp']//a[@data-qa='vacancy-serp__vacancy-title']/@href",
            self.vacancy_parse
        )

    def vacancy_parse(self, response):
        loader = HhVacancyLoader(response=response)  # можно передать также и Item class
        vacancy_data = {
            'title': "//div[@class='vacancy-title']/h1[@class='bloko-header-1']/text()",
            'salary': "//div[@class='vacancy-title']//span[@data-qa='bloko-header-2']/text()",
            'description': '//div[@data-qa="vacancy-description"]//text()',
            'key_skills': "//div[@class= 'vacancy-description']//div[@class= 'bloko-tag-list']//text()",
            'author': "//div[@class= 'vacancy-company__details']//text()",
            'author_url': "//div[@class= 'vacancy-company__details']/a[@class= 'vacancy-company-name']/@href",
        }
        for key, value in vacancy_data.items():
            loader.add_xpath(key, value)
        yield loader.load_item()  # отправка данных на Pipeline

        author = {
            'name': response.xpath(
                        "//div[@class= 'vacancy-company__details']//text()"
                    ).extract_first(),
            'url': response.xpath(
                    "//div[@class= 'vacancy-company__details']/a[@class= 'vacancy-company-name']/@href"
                    ).extract_first()
        }
        yield response.follow(author['url'], callback=self.author_parse)

    def author_parse(self, response):
        loader = HhEmployerLoader(response=response)  # можно передать также и Item class
        loader.add_value('id', response.url.split("/")[-1])
        employer_data = {
            'name': "//div[@class= 'company-header']//h1[@class= 'bloko-header-1']//text()",
            'site': "//div[@class='employer-sidebar-wrapper']//a[@data-qa='sidebar-company-site']/@href",
            'activity': "//div[@class='employer-sidebar-wrapper']//div[@class='employer-sidebar-block']/p/text()",
            'description': "//div[@class='company-description']//text()",
        }
        for key, value in employer_data.items():
            loader.add_xpath(key, value)
        yield loader.load_item()  # отправка данных на Pipeline

        author_id = response.url.split("/")[-1]
        params = copy(self.vacancies_api_list_params)
        params["currentEmployerId"] = author_id
        yield response.follow(
            self.vacancies_api_path + "?" + urlencode(params),
            callback=self.vacancies_api_parse,
            cb_kwargs=params
        )

    def vacancies_api_parse(self, response, **params):
        data = response.json()
        if data['@hasNextPage']:
            params['page'] +=1
            yield response.follow(
                self.vacancies_api_path + "?" + urlencode(params),
                callback=self.vacancies_api_parse,
                cb_kwargs=params
            )
        for vacancy in data['vacancies']:
            yield response.follow(
                vacancy["links"]["desktop"],
                callback=self.vacancy_parse
            )


#закоментаренные строки ниже оставлены осознанно
        # title = response.xpath(
        #     "//div[@class='vacancy-title']/h1[@class='bloko-header-1']/text()"
        # ).extract_first()
        # salary = response.xpath("//div[@class='vacancy-title']//span[@data-qa='bloko-header-2']/text()").extract_first()
        # description = dict(
        #                     enumerate(
        #                         response.xpath(
        #                             "//div[@class= 'vacancy-description']//div[@class= 'vacancy-section']//text()"
        #                         ).extract()
        #                     )
        #              )
        # key_skils = response.xpath(
        #                 "//div[@class= 'vacancy-description']//div[@class= 'bloko-tag-list']//text()"
        #             ).extract()


# закоментаренные строки ниже оставлены осознанно
#         author_name = ' '.join(
#                             response.xpath(
#                                 "//div[@class= 'company-header']//h1[@class= 'bloko-header-1']//text()"
#                             ).extract()
#                     )
#         author_site = response.xpath("//div[@class='employer-sidebar-wrapper']"
#                                      "//a[@data-qa='sidebar-company-site']/@href"
#                     ).get()
#         author_activity = response.xpath("//div[@class='employer-sidebar-wrapper']"
#                                          "//div[@class='employer-sidebar-block']/p/text()"
#                     ).extract()
#         author_description = ''.join(
#                                 response.xpath(
#                                     "//div[@class='company-description']//text()"
#                                 ).extract()
#                             ).replace(u'\xa0', ' ')