# -*- coding: utf-8 -*-

import re
from urllib import parse

import scrapy
from scrapy.http import Request


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
        post_urls = response.css('#archive .floated-thumb .post-thumb a::attr(href)').extract()
        for post_url in post_urls:
            yield Request(url=parse.urljoin(response.url, post_url), callback=self.parse_detail)

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
        title = response.xpath('//div[@class="entry-header"]/h1/text()').extract_first('')
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
