from datetime import datetime

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from PointSearch.sites.lagou.lagou_Item import LaGouJobItem, LaGouJobItemLoader
from PointSearch.utils.common import get_md5


class LaGouJobSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['https://www.lagou.com/']
    agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, " \
            "like Gecko) Chrome/70.0.3538.102 Safari/537.36"
    custom_settings = {
        "COOKIES_ENABLED": False,
        "DOWNLOAD_DELAY": 1,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
            'Cookie': 'JSESSIONID=ABAAABAABEEAAJA8054290E188D139923553434AA4C07F1; _ga=GA1.2.1737'
                      '868323.1546261474; _gid=GA1.2.94072325.1546261474; _gat=1; user_trace_token'
                      '=20181231210434-9ec25d04-0cfc-11e9-ae7e-5254005c3644; LGSID=20181231210434-9ec26'
                      '034-0cfc-11e9-ae7e-5254005c3644; PRE_UTM=; PRE_HOST=www.baidu.com; PRE_SITE='
                      'https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3DgkYRgGmu9Awltg9xR8mBbW3fNWWvxUwGMmEgioosbdm%2'
                      '6ck%3D8235.9.127.247.106.396.319.177%26shh%3Dwww.baidu.com%26sht%3Dbaidu%26'
                      'wd%3D%26eqid%3Da8cec54300062e4e000000065c2a13d1; PRE_LAND=https%3A%2F%2F'
                      'www.lagou.com%2F; LGRID=20181231210434-9ec262a8-0cfc-11e9-ae7e-5254005c3644;'
                      ' LGUID=20181231210434-9ec26341-0cfc-11e9-ae7e-5254005c3644; index_location_city'
                      '=%E5%85%A8%E5%9B%BD; Hm_lvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1546261478;'
                      ' Hm_lpvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1546261478',
            'Host': 'www.lagou.com',
            'Origin': 'https://www.lagou.com',
            'Referer': 'https://www.lagou.com/',
            'User-Agent': agent,
        }
    }

    rules = (
        Rule(LinkExtractor(allow=r'jobs/\d+.html'), callback='parse_content', follow=True),
    )

    @staticmethod
    def parse_content(response):
        item_loader = LaGouJobItemLoader(item=LaGouJobItem(), response=response)
        item_loader.add_css("title", ".job-name::attr(title)")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_css("salary_min", ".job_request .salary::text")
        item_loader.add_xpath("job_city", "//*[@class='job_request']/p/span[2]/text()")
        item_loader.add_xpath("work_years_min", "//*[@class='job_request']/p/span[3]/text()")
        item_loader.add_xpath("degree_need", "//*[@class='job_request']/p/span[4]/text()")
        item_loader.add_xpath("job_type", "//*[@class='job_request']/p/span[5]/text()")
        item_loader.add_css("tags", '.position-label li::text')
        item_loader.add_css("publish_time", ".publish_time::text")
        item_loader.add_css("job_advantage", ".job-advantage p::text")
        item_loader.add_css("job_desc", ".job_bt div")
        item_loader.add_css("job_addr", ".work_addr")
        item_loader.add_css("company_name", "#job_company dt a img::attr(alt)")
        item_loader.add_css("company_url", "#job_company dt a::attr(href)")
        item_loader.add_value("crawl_time", datetime.now())

        job_item = item_loader.load_item()

        return job_item
