# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter

import pymongo  # импорт библиотеки работу с MongoDb


class GbParsePipeline:  # в этом Pipeline можно сделать дополнительную обработку данных. обогатить их
    # и передать затем в следующий Pipeline, согласно приоритету обработки заданному в Settings

    def process_item(self, item, spider):

        return item


class GbMongoPipeline:  # в этом Pipeline сохраним наши данные, находящиеся в объекте Item
    def __init__(self):
        client_db = pymongo.MongoClient()  # создание экземпляра клиента MongoDB
        self.db = client_db["autoyoula_parse"]  # создаем базу данных, в которой будем сохранять нашу коллекцию данных

    def process_item(self, item, spider):
        self.db["hw_autoyoula_parse"].insert_one(dict(item))  # вставляем данные объекте Item в коллекцию
        return item
