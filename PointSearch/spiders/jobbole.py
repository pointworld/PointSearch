from urllib import parse

import scrapy
from scrapy.http import Request

from PointSearch.sites.jobbole.jobbole_Item import JobBoleBlogItem, JobBoleBlogItemLoader
from PointSearch.utils.common import get_md5


class JobBoleSpider(scrapy.Spider):
    name = "jobbole"
    allowed_domains = ["blog.jobbole.com"]
    start_urls = ['http://blog.jobbole.com/all-posts']

    def parse(self, response):
        """
        1. 获取文章列表页中的文章 url 交给 scrapy 下载并进行解析
        2. 获取下一页的 url 并交给 scrapy 进行下载，下载完成后交给 parse
        """
        post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            # 获取封面图的 url
            image_url = post_node.css("img::attr(src)").extract_first("")
            # post_url 是每一页具体的文章 url
            post_url = post_node.css("::attr(href)").extract_first("")

            yield Request(
                url=parse.urljoin(response.url, post_url),
                meta={"front_image_url": image_url},
                callback=self.parse_content
            )

        # 提取下一页 url
        next_url = response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_url:
            # 如果存在 next url 就调用下载下一页，回调 parse 函数会找出下一页的 url
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    @staticmethod
    def parse_content(response):
        jobbole_item = JobBoleBlogItem()

        # 通过 item loader 加载 item
        front_image_url = response.meta.get("front_image_url", "")
        item_loader = JobBoleBlogItemLoader(item=jobbole_item, response=response)

        # 通过 css 选择器将后面的指定规则进行解析
        item_loader.add_css("title", ".entry-header h1::text")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_css("create_date", "p.entry-meta-hide-on-mobile::text")
        item_loader.add_value("front_image_url", [front_image_url])
        item_loader.add_css("praise_nums", ".vote-post-up h10::text")
        item_loader.add_css("comment_nums", "a[href='#article-comment'] span::text")
        item_loader.add_css("fav_nums", ".bookmark-btn::text")
        item_loader.add_css("tags", "p.entry-meta-hide-on-mobile a::text")
        item_loader.add_css("content", "div.entry")

        # 调用这个方法来对规则进行解析生成 item 对象
        jobbole_item = item_loader.load_item()

        # 已经填充好了值调用 yield 传输至 pipeline
        yield jobbole_item
