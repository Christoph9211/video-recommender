import scrapy


class LesbianSpider(scrapy.Spider):
    name = "lesbian"
    allowed_domains = ["eporner.com"]
    start_urls = ["https://eporner.com"]

    def parse(self, response):
        pass
