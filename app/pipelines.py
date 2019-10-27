import json
from scrapy import signals
from scrapy.crawler import CrawlerRunner

from .spiders.website_spider import GenericSpider
from .settings import WebsiteSettings
from .embeddings import Embeddings


class MyCrawlerRunner(CrawlerRunner):
    """
    Crawler object that collects items and returns output after finishing crawl.
    """
    def crawl(self, crawler_or_spidercls, *args, **kwargs):
        # keep all items scraped
        self.items = []

        # create crawler (Same as in base CrawlerProcess)
        crawler = self.create_crawler(crawler_or_spidercls)

        # handle each item scraped
        crawler.signals.connect(self.item_scraped, signals.item_scraped)

        # create Twisted.Deferred launching crawl
        dfd = self._crawl(crawler, *args, **kwargs)

        # add callback - when crawl is done cal return_items
        dfd.addCallback(self.return_items)
        return dfd

    def item_scraped(self, item, response, spider):
        self.items.append(item)

    def return_items(self, result):
        return self.items

def return_spider_output(output):
    """
    :param output: items scraped by CrawlerRunner
    :return: json with list of items
    """

    print('Deferred 1')
    # this just turns items into dictionaries
    # you may want to use Scrapy JSON serializer here
    return [dict(item) for item in output]


def return_company_embedding(company_data):
    """
    function
    :param company_data: scraped data for the company, list of dictionaries
    :return:
    """

    print('Deferred 2')
    embed = Embeddings()
    company_embedding = embed.create_single_embedding(company_data)
    company_dict = json.dumps({'company_embedding': company_embedding})

    return company_dict


class Pipeline:

    """
    Brings together all the scrapy components
    """

    def __init__(self, overwrite):
        self.scraper = GenericSpider()
        self.overwrite = overwrite

    def run(self, url):

        """
        Carry out scrape of website
        :param url: URL string
        :return: None
        """

        scrape_file_location = 'app/scrape_output/pharmaforesight.json'

        # conduct scrape
        print(1)
        runner = MyCrawlerRunner(settings=WebsiteSettings().generate_settings_dict(file_location=scrape_file_location))
        print(2)
        deferred = runner.crawl(self.scraper.create(url))
        print(3)
        deferred.addCallback(return_spider_output)
        print(4)
        deferred.addCallback(return_company_embedding)
        return deferred
