# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class JobBoleArticleItem(scrapy.Item):
    title = scrapy.Field()
    content = scrapy.Field()
    tags = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    cover_url = scrapy.Field()
    cover_path = scrapy.Field()
    fav_nums = scrapy.Field()
    praise_nums = scrapy.Field()
    comment_nums = scrapy.Field()
    create_date = scrapy.Field()
