# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import codecs
import json

from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi

import MySQLdb
import MySQLdb.cursors


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


class JsonWithEncodingPipeline(object):
    """
    自定义 json 文件的导出
    """

    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + '\n'
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()


class MysqlPipeline(object):
    # 采用同步的机制写入数据
    def __init__(self):
        self.conn = MySQLdb.connect('192.168.1.128', 'root', 'pointworld', 'article_spider', charset='utf8',
                                    use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into  jobbole_article(url_object_id, title, url, create_date, fav_nums) VALUES (%s, %s, %s, %s, %s)
        """
        self.cursor.execute(insert_sql,
                            (item['url_object_id'], item['title'], item['url'], item['create_date'], item['fav_nums']))
        self.conn.commit()
        return item


class MysqlTwistedPipeline(object):
    # 采用异步的方式写入数据库
    def __init__(self, db_pool):
        self.db_pool = db_pool

    @classmethod
    def from_settings(cls, settings):
        db_params = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWORD'],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )

        db_pool = adbapi.ConnectionPool('MySQLdb', **db_params)

        return cls(db_pool)

    def process_item(self, item, spider):
        """
        使用 twisted 将 MySQL 插入变成异步执行
        :param item:
        :param spider:
        :return:
        """
        query = self.db_pool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)
        return item

    def handle_error(self, failure, item, spider):
        # 处理异步插入的异常
        print(failure)

    def do_insert(self, cursor, item):
        # 执行具体的插入
        insert_sql = """
            insert into  jobbole_article(
                url_object_id, title, content, tags, url, cover_url, fav_nums, 
                praise_nums, comment_nums, create_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (
            item['url_object_id'], item['title'], item['content'], item['tags'], item['url'], item['cover_url'],
            item['fav_nums'], item['praise_nums'], item['comment_nums'], item['create_date']
        ))


class JsonExporterPipeline(object):
    """
    调用 scrapy 提供的 json exporter 导出 json 文件
    """

    def __init__(self):
        self.file = open('article_export.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if 'cover_url' in item:
            for ok, value in results:
                item['cover_path'] = value['path']
        return item
