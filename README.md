# 搜索引擎 PointSearch（ElasticSearch or Mysql）

>Scrapy1.5.1(爬取数据) + ElasticSearch6.3.2(存储数据并提供对外 Restful Api) + Django 打造搜索引擎网站 (可配置数据存入 Mysql)

**本仓库为爬虫端数据入库 ElasticSearch 代码**,实现整个搜索需要结合 Django 网站端项目

## 可用功能

1. 伯乐在线，拉勾职位，知乎爬虫存入 Mysql & 存入 ElasticSearch
2. 全文搜索(需结合网站端一起使用)，搜索建议，我的搜索记录，搜索词高亮标红，搜索结果底部分页
3. Redis 实现的实时三站已爬取数目展示，热门搜索 Top-5

## 项目外部依赖

ElasticSearch6.3.2 + ElasticSearch-analysis-ik(中文分词) + Redis + MySQL

## 长期维护更新

定期对伯乐在线博客文章，拉勾网职位，知乎的问题回答爬取进行了维护更新，并进行了存入 Mysql 以及 存入 ElasticSearch6 的测试。

## 如何开始使用？

安装 ElasticSearch6.3.2，配置 ElasticSearch-analysis-ik 插件，安装 Redis(可选配置 ElasticSearch-head)

```
git clone https://github.com/pointworld/PointSearch
# 新建数据库 point_search; Navicat 导入 mysql 文件; 修改 config_template 配置信息,去除 _template 后缀。
# 执行 sites/es_* 配置 ELasticPipeline

cd PointSearch
pip install -r requirements.txt
scrapy crawl zhihu
scrapy crawl lagou
scrapy crawl jobbole
```

简书相关文集地址(已过期，只有一定参考意义，最好的读物是源码!):https://www.jianshu.com/nb/11202633
