import datetime
import re

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Join
from elasticsearch_dsl import connections
from w3lib.html import remove_tags

from PointSearch.items import MysqlItem, ElasticSearchItem
from PointSearch.settings import SQL_DATETIME_FORMAT
from PointSearch.sites.jobbole.es_jobbole import JobBoleBlogIndex
from PointSearch.utils.common import real_time_count
from PointSearch.utils.es_utils import generate_suggests
from PointSearch.utils.mysql_utils import fun_sql_insert
from PointSearch.utils.string_util import return_value, get_nums

# 与 ElasticSearch 进行连接，生成搜索建议
es_jobbole_blog = connections.create_connection(JobBoleBlogIndex)

JOBBOLE_COUNT_INIT = 0


def remove_comment_tags(value):
    """
    去除标签中提取的评论方法
    """
    if "评论" in value:
        return ""
    else:
        return value


class JobBoleBlogItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


class JobBoleBlogItem(scrapy.Item, MysqlItem, ElasticSearchItem):
    """
    伯乐在线 Item
    命名规范: 域名+内容+Item
    """
    field_list = ['title', 'create_date', 'url', 'url_object_id', 'front_image_url',
                  'praise_nums', 'comment_nums', 'fav_nums', 'tags', 'content', 'crawl_time']

    duplicate_key_update = ['praise_nums', 'comment_nums', 'crawl_time', 'fav_nums']

    table_name = 'jobbole_article'

    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(output_processor=MapCompose(return_value))
    praise_nums = scrapy.Field()
    comment_nums = scrapy.Field(input_processor=MapCompose(get_nums))
    fav_nums = scrapy.Field(input_processor=MapCompose(get_nums))
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor=Join(",")
    )
    content = scrapy.Field()
    create_date = scrapy.Field()
    crawl_time = scrapy.Field()

    def clean_data(self):
        if self["front_image_url"]:
            self["front_image_url"] = self["front_image_url"][0]
        self["crawl_time"] = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)
        date_str = self["create_date"].strip().replace("·", "").strip()
        self["create_date"] = datetime.datetime.strptime(date_str, "%Y/%m/%d").date()
        value = self["praise_nums"]
        match_re = re.match(".*?(\d+).*", value)
        if match_re:
            nums = int(match_re.group(1))
        else:
            nums = 0
        self["praise_nums"] = nums

    def save_to_mysql(self):
        self.clean_data()
        insert_sql = """insert into jobbole_article(title,create_date,url,url_object_id,front_image_url,praise_nums,comment_nums,fav_nums,tags,content,crawl_time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE praise_nums=VALUES(praise_nums), comment_nums=VALUES(comment_nums), crawl_time=VALUES(crawl_time), fav_nums=VALUES(fav_nums)"""
        sql_params = (
            self["title"],
            self["create_date"],
            self["url"],
            self["url_object_id"],
            self["front_image_url"],
            self["praise_nums"],
            self["comment_nums"],
            self["fav_nums"],
            self["tags"],
            self["content"],
            self["crawl_time"],
        )
        return insert_sql, sql_params

    def save_to_es(self):
        """
        保存伯乐在线文章到 es 中
        """
        self.clean_data()
        blog = JobBoleBlogIndex()
        blog.title = self['title']
        blog.create_date = self["create_date"]
        blog.content = remove_tags(self["content"])
        blog.front_image_url = self["front_image_url"]
        blog.praise_nums = self["praise_nums"]
        blog.fav_nums = self["fav_nums"]
        blog.comment_nums = self["comment_nums"]
        blog.url = self["url"]
        blog.tags = self["tags"]
        blog.meta.id = self["url_object_id"]
        # 在保存数据时必须传入 suggest
        blog.suggest = generate_suggests(
            es_jobbole_blog, ((blog.title, 10), (blog.tags, 6), (blog.content, 4))
        )
        real_time_count('jobbole_blog_count', JOBBOLE_COUNT_INIT)
        blog.save()

    def help_fields(self):
        for field in self.field_list:
            print(field, "= scrapy.Field()")


if __name__ == '__main__':
    instance = JobBoleBlogItem()
    print(instance.help_fields())
    print("*" * 30)
    print("self.data_clean()")
    sql, params = fun_sql_insert(
        field_list=instance.field_list,
        duplicate_key_update=instance.duplicate_key_update,
        table_name=instance.table_name
    )
    print(sql)
    print(params)
