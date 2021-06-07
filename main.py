from scrapy.crawler import CrawlerProcess  # процесс управляющий пауками
from scrapy.settings import Settings  # импорт класса настроек

from gb_parse.spiders.autoyoula import AutoyoulaSpider  # импорт нашего паука

if __name__ == '__main__':
    crawler_settings = Settings()  # инициализация класса Settings
    crawler_settings.setmodule('gb_parse.settings')  # передаем в класс наши настройки
    crawler_process = CrawlerProcess(settings=crawler_settings)  # инициализация процесса с нашими настройками
    crawler_process.crawl(AutoyoulaSpider)  # добавляем нашего паука, передав в качестве параметра класс (!) нашего
                                            # паука. Таких пауков можно добавлять много. После стартовать процесс,
                                            # который будет ими управлять ->
    crawler_process.start()