import scrapy
from urllib.parse import quote
from ..items import VideoScrapperItem as VideoItem

class HqPornerSpider(scrapy.Spider):
    name = "hqporner"
    custom_settings = {"DOWNLOAD_DELAY": 0.7}

    def __init__(self, query, max_results=20):
        super().__init__(query=query)
        self.query       = query
        self.max_results = int(max_results)

    def start_requests(self):
        url = f"https://www.hqporner.com/search/{quote(self.query)}/"
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        for idx, link in enumerate(
            response.xpath("//div[contains(@class,'searchResult')]//a[starts-with(@href,'/video/')]"), 
            1
        ):
            if idx > self.max_results:
                break
            title = (link.attrib.get("title") or link.xpath("text()").get()).strip()
            yield VideoItem(
                title=title,
                url=response.urljoin(link.attrib["href"]),
                source="hqporner",
                description="",
            )
