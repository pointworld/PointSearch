# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import re
from datetime import datetime

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join


class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


def date_convert(value):
    try:
        create_date = datetime.strftime(value, '%Y/%m/%d')
    except Exception as e:
        create_date = datetime.now().date()
    return create_date


def get_nums(value):
    match_re = re.match(".*?(\d+).*", value)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0
    return nums


def remove_comment_tags(value):
    """
    去掉 tag 中提取的“评论”
    :param value:
    :return:
    """
    if '评论' in value:
        return ''
    else:
        return value


def return_value(value):
    return value


class ArticleItemLoader(ItemLoader):
    """
    自定义 itemLoader
    """
    default_output_processor = TakeFirst()


class JobBoleArticleItem(scrapy.Item):
    url_object_id = scrapy.Field()
    title = scrapy.Field(
        input_processor=MapCompose(lambda x: x + '-point')
    )
    content = scrapy.Field()
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        ouput_processor=Join(','),
    )
    url = scrapy.Field()
    cover_url = scrapy.Field(
        ouput_processor=MapCompose(return_value)
    )
    cover_path = scrapy.Field()
    fav_nums = scrapy.Field(input_processor=MapCompose(get_nums))
    praise_nums = scrapy.Field(input_processor=MapCompose(get_nums))
    comment_nums = scrapy.Field(input_processor=MapCompose(get_nums))
    create_date = scrapy.Field(input_processor=MapCompose(date_convert))
