import json
import re
import os
from os import path
from datetime import datetime
from urllib import parse

import scrapy
from scrapy.loader import ItemLoader

from PointSearch.sites.zhihu.zhihu_item import ZhiHuQuestionItem, ZhiHuAnswerItem
from PointSearch.utils.common import get_md5
from ..config import ZHIHU_PHONE, ZHIHU_PASSWORD


class ZhiHuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['https://www.zhihu.com/']

    # question 的第一页 answer 的请求 url
    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B%2A%5D.is_normal%2' \
                       'Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2' \
                       'Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2' \
                       'Cis_thanked%2Cis_nothelp%2Cis_labeled%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2' \
                       'A%5D.author.follower_count%2Cbadge%5B%2A%5D.topics&limit={1}&offset={2}&sort_by=default'

    headers = {
        'HOST': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/70.0.3538.102 Safari/537.36',
    }

    custom_settings = {
        "COOKIES_ENABLED": True,
        "DOWNLOAD_DELAY": 1.5,
    }

    def start_requests(self):
        """
        爬虫入口
        :return:
        """
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import time

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')

        chromeDriver = webdriver.Chrome(
            chrome_options=chrome_options,
        )

        chromeDriver.get("https://www.zhihu.com/signin")
        chromeDriver.find_element_by_css_selector('.SignFlow-accountInput.Input-wrapper input').send_keys(ZHIHU_PHONE)
        time.sleep(1)
        chromeDriver.find_element_by_css_selector('.SignFlow-password input').send_keys(ZHIHU_PASSWORD)
        time.sleep(2)
        chromeDriver.find_element_by_css_selector('.Button.SignFlow-submitButton').click()
        time.sleep(3)
        chromeDriver.get('https://www.zhihu.com/')
        time.sleep(6)
        zhihu_cookies = chromeDriver.get_cookies()
        print(zhihu_cookies)

        cookie_dict = {}

        import pickle
        for cookie in zhihu_cookies:
            base_path = path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cookies')
            f = open(base_path + "/zhihu/" + cookie['name'] + '.zhihu', 'wb')
            pickle.dump(cookie, f)
            f.close()
            cookie_dict[cookie['name']] = cookie['value']

        chromeDriver.close()

        # 会调用 parse 方法，该请求参数可以没有 callback，但必须设置 headers
        return [scrapy.Request(url=self.start_urls[0], dont_filter=True, cookies=cookie_dict, headers=self.headers)]

    def parse(self, response):
        """
        提取出当前 HTML 页面中所有的 url
        如果提取的 url 中含有 /question/xxx，则下载之后直接进入解析函数，否则递归调用 parse 函数
        """

        all_urls = response.css("a::attr(href)").extract()
        # 使列表中的每个 URL 都是完整的路径
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        # 过滤掉不以 https 开头的 URL
        all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)

        for url in all_urls:
            # 具体问题以及具体答案的 url 我们都要提取出来，或关系
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                # 如果提取到 question 相关的页面，则下载后交由提取函数（self.parse_question）进行提取
                request_url = match_obj.group(1)
                yield scrapy.Request(request_url, headers=self.headers, callback=self.parse_question)
            else:
                # 如果不是 question 页面，则交给函数（self.parse）递归跟踪
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)

    def parse_question(self, response):
        """
        处理 question 页面，从页面中提取出具体的 question item
        :param response:
        :return:
        """

        # ...<h1 class="QuestionHeader-title">xxx</h1>...
        if "QuestionHeader-title" in response.text:
            # response.url: https://www.zhihu.com/question/19581624
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
            if match_obj:
                # 19581624
                question_id = int(match_obj.group(2))

                item_loader = ItemLoader(item=ZhiHuQuestionItem(), response=response)

                item_loader.add_value("url_object_id", get_md5(response.url))
                item_loader.add_value("question_id", question_id)
                item_loader.add_css("title", "h1.QuestionHeader-title::text")
                item_loader.add_xpath("content", "//*[@id='root']/div/main/div/div[1]/div[2]"
                                                 "/div[1]/div[1]/div[2]/div/div/div/span/text()")
                item_loader.add_css("topics", ".QuestionHeader-topics .Tag.QuestionTopic .Popover div::text")
                item_loader.add_css("answer_num", ".List-headerText span::text")
                item_loader.add_css("comments_num", ".QuestionHeader-Comment button::text")
                # 这里的 watch_user_num 包含 Watch 和 click，在 clean data 时会进行分离
                item_loader.add_css("watch_user_num", ".NumberBoard-itemValue ::text")
                item_loader.add_value("url", response.url)

                question_item = item_loader.load_item()

                # 向后台发起具体 answer 的接口请求
                yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0), headers=self.headers,
                                     callback=self.parse_answer_start)
                yield question_item
            else:
                # TODO
                pass
        else:
            # TODO
            pass

    def parse_answer_start(self, response):
        """
        处理 answer 页面
        :param response:
        :return:
        """

        ans_json = json.loads(response.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        # 提取 answer 的具体字段
        for answer in ans_json["data"]:
            url_object_id = get_md5(url=answer["url"])
            answer_id = answer["id"]
            question_id = answer["question"]["id"]
            author_id = answer["author"]["id"] if "id" in answer["author"] else None
            author_name = answer["author"]["name"] if "name" in answer["author"] else None
            content = answer["excerpt"] if "excerpt" in answer else ""
            really_url = "https://www.zhihu.com/question/{0}/answer/{1}".format(answer["question"]["id"],
                                                                                answer["id"])
            create_time = answer["created_time"]
            updated_time = answer["updated_time"]

            yield scrapy.Request(really_url, headers=self.headers,
                                 callback=self.parse_answer_end, meta={'url_object_id': url_object_id,
                                                                       'answer_id': answer_id,
                                                                       'question_id': question_id,
                                                                       'author_id': author_id,
                                                                       'author_name': author_name,
                                                                       'content': content,
                                                                       'create_time': create_time,
                                                                       'updated_time': updated_time})
        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer_start)

    def parse_answer_end(self, response):
        """
        从 answer 页面中提取出具体的 answer item
        :param response:
        :return:
        """
        answer_item = ZhiHuAnswerItem()
        answer_item["url_object_id"] = response.meta.get("url_object_id", "")
        answer_item["answer_id"] = response.meta.get("answer_id", "")
        answer_item["question_id"] = response.meta.get("question_id", "")
        answer_item["author_id"] = response.meta.get("author_id", "")
        answer_item["author_name"] = response.meta.get("author_name", "")
        answer_item["content"] = response.meta.get("content", "")
        answer_item["url"] = response.meta.get("url", "")
        answer_item["create_time"] = response.meta.get("create_time", "")
        answer_item["update_time"] = response.meta.get("updated_time", "")
        answer_item["comments_num"] = response.css(".Button.VoteButton.VoteButton--up::text")[0].extract()
        answer_item["praise_num"] = response.css(".Button.ContentItem-action.Button--plain."
                                                 "Button--withIcon.Button--withLabel::text")[0].extract()
        answer_item["crawl_time"] = datetime.now()
        yield answer_item
