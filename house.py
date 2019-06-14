# -*- coding: utf-8 -*-
import scrapy


class HouseSpider(scrapy.Spider):
    name = 'house'
    allowed_domains = ['fang.com']
    start_urls = ['http://fang.com/']

    def parse(self, response):
        pass
