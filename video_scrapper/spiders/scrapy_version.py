import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

class EpornerSpider(scrapy.Spider):
    name = "myspider"
    allowed_domains = ["eporner.com"]
    start_urls = ["https://www.eporner.com/"]
    
    rules = (Rule(LinkExtractor(allow=r"Items/"), callback="parse_item", follow=True),)

    def __init__(self, *args, **kwargs):
        super(EpornerSpider, self).__init__(*args, **kwargs)
        self.query = kwargs.get('query')
        self.max_results = kwargs.get('max_results', 10)
        
    async def parse_item(self, response):
        item = {}
        item["domain_id"] = response.xpath('//input[@id="sid"]/@value').get()
        item["name"] = response.xpath('//div[@id="name"]').get()
        item["description"] = response.xpath('//div[@id="description"]').get()
        item["url"] = response.xpath('//link[@rel="canonical"]/@href').get()
        item["title"] = response.xpath('//title/text()').get().strip()
        return item
    
    def parse(self, item):
        video_data = []
        for link in item.css("div.mbunder p.mbtit a[href^='/video-']"):
            href = link.css("::attr(href)").get()
            title = link.css("::attr(title)").get() or link.css("::text").get().strip()
            if not href or not title:
                continue

            full_url = f"https://www.eporner.com{href}"
            if any(video["url"] == full_url for video in video_data):
                continue

            video_data.append({
                "title": title,
                "url": full_url,
                "source": "eporner",
                "description": "",
            })

            if len(video_data) >= self.max_results:
                break

        yield {
            "videos": video_data
        }