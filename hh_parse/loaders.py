from urllib.parse import urljoin
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst  # возвращает первый не пустой объект
from itemloaders.processors import MapCompose  # организует конвейер обработок, callable object


def take_first(items):
    return items[0]


def list_2_text(items):
    return "".join(items)


def clear_text(text_item: str):
    cls_text = text_item.replace('\xa0', ' ')
    return cls_text


def create_author_url(short_url:str) ->str:
    full_url = ""
    if short_url:
        full_url = urljoin("https://hh.ru/", short_url)
    return full_url


class HhVacancyLoader(ItemLoader):
    default_item_class = dict
    title_out = TakeFirst()  # корень (в данном случае - title, url и тд) должен соответствовать
    url_out = TakeFirst()    # переменным добавленным в лоадер через add_value
    salary_in = MapCompose(clear_text)
    description_in = MapCompose(clear_text)
    key_skills_in = MapCompose(clear_text)
    author_out = TakeFirst()
    author_url_in = MapCompose(create_author_url)
    author_url_out = TakeFirst()
    item_type_out = TakeFirst()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get("response"):
            self.add_value("url", self.context["response"].url)
        self.add_value("item_type", "vacancy")


class HhEmployerLoader(ItemLoader):
    default_item_class = dict
    id_out = TakeFirst()
    url_out = TakeFirst()
    item_type_out = TakeFirst()
    name_in = MapCompose(list_2_text)
    name_out = TakeFirst()
    site_out = TakeFirst()
    activity_in = MapCompose(clear_text)
    description_in = MapCompose(clear_text, list_2_text)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get("response"):
            self.add_value("url", self.context["response"].url)
        self.add_value("item_type", "company")