# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import MySQLdb
import MySQLdb.cursors
from twisted.enterprise import adbapi


class PointSearchPipeline(object):
    @staticmethod
    def process_item(item, spider):
        return item


class MysqlTwistedPipeline(object):
    """
    通用的数据库保存 Pipeline
    """

    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        """
        自定义组件或扩展很有用的方法: 这个方法名字固定, 是会被 scrapy 调用的
        这里传入的 cls 是指当前的 class
        """
        db_params = dict(
            host=settings["MYSQL_HOST"],
            db=settings["MYSQL_DBNAME"],
            user=settings["MYSQL_USER"],
            passwd=settings["MYSQL_PASSWORD"],
            charset='utf8mb4',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )
        # 连接池 ConnectionPool
        db_pool = adbapi.ConnectionPool("MySQLdb", **db_params)

        # 此处相当于实例化 pipeline, 要在 init 中接收
        return cls(db_pool)

    def process_item(self, item, spider):
        """
        使用 twisted 将 mysql 插入变成异步执行
        参数1: 我们每个 item 中自定义一个函数，里面可以写我们的插入数据库的逻辑
        """
        query = self.dbpool.runInteraction(self.do_insert, item)
        # 添加自己的处理异常的函数
        query.addErrback(self.handle_error, item, spider)

    def do_insert(self, cursor, item):
        """
        执行具体的插入
        根据不同的 item 构建不同的 sql 语句并插入到 mysql 中
        """
        insert_sql, params = item.save_to_mysql()
        cursor.execute(insert_sql, params)

    @staticmethod
    def handle_error(failure, item, spider):
        # 处理异步插入的异常
        print(failure)


class ElasticSearchPipeline(object):
    """
    通用的 ELasticSearch 存储方法
    """

    def process_item(self, item, spider):
        item.save_to_es()
        return item
