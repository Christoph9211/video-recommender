import scrapy
from urllib.parse import quote
from ..items import VideoScrapperItem as VideoItem

class EpornerSpider(scrapy.Spider):
    name = "eporner"
    custom_settings = {"DOWNLOAD_DELAY": 0.7}
    
    def __init__(self, query, max_results=20):
        super().__init__(query=query)
        self.query        = query
        self.max_results  = int(max_results)

    def start_requests(self):
        q = quote(self.query.replace(" ", "-"))
        url = f"https://www.eporner.com/search/{q}/"
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        sel = response.xpath("//div[contains(@class,'mbunder')]//p[contains(@class,'mbtit')]/a")
        for idx, link in enumerate(sel, 1):
            if idx > self.max_results:
                break

            item = VideoItem(
                title       = (link.attrib.get("title") or link.xpath("text()").get()).strip(),
                url         = response.urljoin(link.attrib["href"]),
                source      = "eporner",
                description = "",
            )
            yield item
