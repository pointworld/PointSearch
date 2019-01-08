#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

__author__ = 'point'
__date__ = '2018-12-29'

import sys
import os

from scrapy.cmdline import execute

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# execute(['scrapy', 'crawl', 'jobbole'])
# execute(['scrapy', 'crawl', 'lagou'])
execute(['scrapy', 'crawl', 'zhihu'])
