# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy import Request
from .settings import BOT_NAME
from pymongo import MongoClient
from scrapy.pipelines.images import ImagesPipeline


class InstParsePipeline:
    def process_item(self, item, spider):
        return item


class InstMongoPipeline:

    def __init__(self):
        client = MongoClient()
        self.db = client[BOT_NAME]

    def process_item(self, item, spider):
        collection_name = f"{spider.name}_{item.get('item_type', '')}"
        self.db[collection_name].insert_one(item)
        return item


class InstImageDownloadPipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        images = item["data"].get("image_versions2", [])
        if images:
            for itm in images["candidates"]:
                if itm.get("url"):
                    yield Request(itm.get("url"))

    def item_completed(self, results, item, info):
        if results:
            item['photos'] = [itm[1] for itm in results]
        return item
