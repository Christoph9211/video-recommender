import scrapy
# from urllib.parse import quote
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule
# from ..items import VideoScrapperItem as VideoItem

class PorntrexSpider(scrapy.Spider):
    name = "porntrex"
    custom_settings = {"DOWNLOAD_DELAY": 0.7}
    allowed_domains = ["porntrex.com"]
    start_urls = ["https://www.porntrex.com/"]
    
    rules = (Rule(LinkExtractor(allow=r"Items/"), callback="parse_item", follow=True),)

    def __init__(self, *args, **kwargs):
        super(PorntrexSpider, self).__init__(*args, **kwargs)
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

            full_url = f"https://www.porntrex.com{href}"
            if any(video["url"] == full_url for video in video_data):
                continue

            video_data.append({
                "title": title,
                "url": full_url,
                "source": "porntrex",
                "description": "",
            })

            if len(video_data) >= self.max_results:
                break

        yield {
            "videos": video_data
        }

    # def start_requests(self, query=None):
    #     if not query:
    #         raise ValueError("Query parameter is required")
    #     url = f"https://www.porntrex.com/search/{quote(query)}"
    #     yield scrapy.Request(url, callback=self.parse)

    # def parse(self, response):
    #     for idx, link in enumerate(
    #         response.xpath("//div[contains(@class,'searchResult')]//a[starts-with(@href,'/video/')]"),
    #         1
    #     ):
    #         if idx > self.max_results:
    #             break
    #         title = (link.attrib.get("title") or link.xpath("text()").get()).strip()
    #         yield VideoItem(
    #             title=title,
    #             url=response.urljoin(link.attrib["href"]),
    #             source="porntrex",
    #             description="",
    #         )
