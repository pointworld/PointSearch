from elasticsearch_dsl import Text, Date, Keyword, Integer, Document, Completion, analyzer
from elasticsearch_dsl.connections import connections

connections.create_connection(hosts=["localhost"])

my_analyzer = analyzer('ik_smart')


class JobBoleBlogIndex(Document):
    """
    伯乐在线文章类型
    """
    url_object_id = Keyword()
    url = Keyword()
    title = Text(analyzer="ik_max_word")
    content = Text(analyzer="ik_smart")
    tags = Text(analyzer="ik_max_word")
    suggest = Completion(analyzer=my_analyzer)
    front_image_url = Keyword()
    praise_nums = Integer()
    comment_nums = Integer()
    fav_nums = Integer()
    create_date = Date()

    class Index:
        name = 'jobbole_blog'


if __name__ == "__main__":
    JobBoleBlogIndex.init()
