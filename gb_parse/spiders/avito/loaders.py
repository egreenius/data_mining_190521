from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose

from .processor import clean_parameters, to_type, create_author_url


class AvitoRealEstateLoader(ItemLoader):
    default_item_class = dict
    item_type_out = TakeFirst()
    url_out = TakeFirst()
    title_out = TakeFirst()
    price_out = TakeFirst()
    price_in = MapCompose(to_type(float))
    address_out = TakeFirst()
    parameters_in = MapCompose(clean_parameters)
    author_url_in = MapCompose(create_author_url)
    author_url_out = TakeFirst()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get("response"):
            self.add_value("url", self.context["response"].url)
        self.add_value("item_type", "real_estate")
