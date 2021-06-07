# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class GbParseItem(Item):
    # определяем поля нашей структуры данных:
    title = Field()
    url = Field()
    price = Field()
    photo = Field()
    features = Field()
    description = Field()
    author = Field()
