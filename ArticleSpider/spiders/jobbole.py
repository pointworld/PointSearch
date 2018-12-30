# -*- coding: utf-8 -*-

import re
from urllib import parse

import scrapy
from scrapy.http import Request

from ..items import JobBoleArticleItem
from ..utils.common import get_md5


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        """
        1. 获取文章列表页中的所有文章 URL，并交给 scrapy 进行下载和解析
        2. 获取下一页的 URL
        3. 重复执行步骤 1 和 2
        :param response:
        :return:
        """

        # 获取列表页中的所有文章 URL，并交给 scrapy 下载和解析
        post_nodes = response.css('#archive .floated-thumb .post-thumb a')
        for post_node in post_nodes:
            cover_url = post_node.css('img::attr(src)').extract_first('')
            post_url = post_node.css('::attr(href)').extract_first('')
            yield Request(url=parse.urljoin(response.url, post_url), meta={'cover_url': cover_url}, callback=self.parse_detail)

        # 提取下一页，并交给 scrapy 进行下载和解析
        next_url = response.css('.next.page-numbers::attr(href)').extract_first('')
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    def parse_detail(self, response):
        """
        提取文章的具体字段
        :param response:
        :return:
        """
        article_item = JobBoleArticleItem()

        title = response.xpath('//div[@class="entry-header"]/h1/text()').extract_first('')
        # 文章封面图
        cover_url = response.meta.get('cover_url', '')
        create_date = response.xpath("//p[@class='entry-meta-hide-on-mobile']/text()").extract_first(
            '').strip().replace("·", "").strip()
        praise_nums = int(response.xpath('//div[@class="post-adds"]/span/h10/text()').extract_first(0))
        fav_nums = response.xpath("//span[contains(@class, 'bookmark-btn')]/text()").extract_first(0)
        match_re = re.match(".*?(\d+).*", fav_nums)
        if match_re:
            fav_nums = int(match_re.group(1))
        else:
            fav_nums = 0

        comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract_first(0)
        match_re = re.match(".*?(\d+).*", comment_nums)
        if match_re:
            comment_nums = int(match_re.group(1))
        else:
            comment_nums = 0

        content = response.xpath("//div[@class='entry']").extract_first('')

        tag_list = response.xpath("//p[@class='entry-meta-hide-on-mobile']/a/text()").extract()
        tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        tags = ",".join(tag_list)

        article_item['title'] = title
        article_item['content'] = content
        article_item['tags'] = tags
        article_item['url'] = response.url
        article_item['url_object_id'] = get_md5(response.url)
        article_item['cover_url'] = [cover_url]
        article_item['fav_nums'] = fav_nums
        article_item['praise_nums'] = praise_nums
        article_item['comment_nums'] = comment_nums
        article_item['create_date'] = create_date

        yield article_item

