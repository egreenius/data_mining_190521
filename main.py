from scrapy.crawler import CrawlerProcess  # импорт класса управляющего процесса
from scrapy.settings import Settings  # импорт класса настроек

from hh_parse.spiders.hh_remote import HhRemoteSpider


if __name__ == '__main__':
    crawler_settings = Settings()  # инициализируем класс Settings
    crawler_settings.setmodule('hh_parse.settings')  # передаем экземпляру класса Settings
    # наш модуль с настройками settings.py
    crawler_process = CrawlerProcess(settings=crawler_settings)  # создаем экземпляр процесса с нашими настройками
    # добавляем процессу паука (или пауков). Передаем в качестве параметра класс паука (не экземпляр!)
    crawler_process.crawl(HhRemoteSpider)
    crawler_process.start()
