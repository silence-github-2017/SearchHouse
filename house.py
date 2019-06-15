# -*- coding: utf-8 -*-
import scrapy
from urllib import request
import re
from SearchHouse.items import EsHouseItem
from SearchHouse.items import NewHouseItem
import json


class HouseSpider(scrapy.Spider):
    name = 'house'
    allowed_domains = ['ke.com']
    start_urls = ['https://www.ke.com/city/']

    def parse(self, response):
        prov_list = response.xpath("//div[@class='city_province']")
        for prov in prov_list:
            prov_name = prov.xpath('.//div/text()').get().strip()
            if not prov_name:
                continue
            ct_list = prov.xpath(".//li/a")
            for ct in ct_list:
                # 存在二手房
                city_name = ct.xpath("./text()").get()
                city_link = "https:" + ct.xpath("./@href").get()
                if city_link.find('fang') == -1:
                    pass
                    # https://jx.fang.ke.com/loupan 新
                    # https://jx.ke.com/ 原始
                    # city_es_link = request.urljoin(city_link, 'ershoufang/')
                    # yield scrapy.Request(
                    #     url=city_es_link, callback=self.es_parser,
                    #     meta={'info': (prov_name, city_name, city_es_link)}
                    # )
                else:
                    pass
                    # 新房
                    city_new_link = request.urljoin(city_link, 'loupan/')
                    # 无二手房
                    yield scrapy.Request(
                        url=city_new_link, callback=self.new_parser,
                        meta={'info': (prov_name, city_name, city_new_link)}
                    )

    def es_parser(self, response):
        prov, city, cur_url = response.meta.get('info')
        house_li = response.xpath("//ul[@class='sellListContent']/li")
        for house in house_li:
            detail_url = house.xpath(".//div[@class='title']/a/@href").get()
            title = house.xpath(".//div[@class='title']/a/text()").get().strip()
            address = house.xpath(".//div[@class='positionInfo']/a/text()").get().strip()
            follow = re.sub("\s|\n", "", house.xpath(".//div[@class='followInfo']//text()").getall()[1])
            info = re.sub("\n\s", "", house.xpath(".//div[@class='houseInfo']//text()").getall()[1])
            level, year, room_type, area, orientations = self.parse_str(info)
            total_price = house.xpath(".//div[@class='totalPrice']//text()").get() + '万'
            per_price = house.xpath(".//div[@class='unitPrice']/span/text()").get()
            items = EsHouseItem(detail_url=detail_url, title=title, address=address,
                                follow=follow, info=info, level=level, year=year, room_type=room_type,
                                area=area, orientations=orientations, total_price=total_price,
                                per_price=per_price, prov=prov, city=city)
            yield items
            # 获取当前页码
            next_page = response.xpath("//div[@class='page-box house-lst-page-box']")
            page_str = next_page.xpath("./@page-data").get()
            cur_page = json.loads(page_str).get('curPage')
            total_page = json.loads(page_str).get('totalPage')
            if cur_page < total_page:
                # 获取下一页url
                temp_url = next_page.xpath("./@page-url").get().split('/')[-1]
                temp_url = re.sub("page", '', temp_url).format(cur_page + 1)
                next_url = cur_url + temp_url
                yield scrapy.Request(url=next_url, callback=self.es_parser, meta={'info': (prov, city, cur_url)})

    def new_parser(self, response):
        # cur_url 当前访问的页面
        prov, city, cur_url = response.meta.get('info')
        house_li = response.xpath("//div[@class='resblock-desc-wrapper']")
        for house in house_li:
            title = house.xpath("./div/a/text()").get()
            address = house.xpath(".//a[@class='resblock-location']//text()").getall()[-1]
            address = re.sub(r"\t|\n", '', address)
            room_count = house.xpath("./a[@class='resblock-room']/span[2]/text()").get()
            if not room_count:
                room_count = ''

            area = house.xpath("./a[@class='resblock-room']/span[last()]/text()").get()
            if not area:
                area = ''
            per_price = re.sub(r"\s", '', ''.join(house.xpath(".//div[@class='main-price']/span/text()").getall()))
            detail_url = cur_url + house.xpath("./div/a/@href").get()[8:]
            total_price = house.xpath(".//div[@class='second']/text()").get()
            if not total_price:
                total_price = ''
            items = NewHouseItem(title=title, address=address, room_count=room_count,
                                 area=area, per_price=per_price, detail_url=detail_url,
                                 total_price=total_price,
                                 prov=prov, city=city)
            yield items
            next_str = response.xpath("//div[@class='page-box']")
            current_page = int(next_str.xpath("./@data-current").get())
            total_page = int(next_str.xpath("./@data-total-count").get())
            if current_page < total_page:
                next_url = cur_url + "pg{}".format(current_page + 1)
                scrapy.Request(url=next_url, callback=self.new_parser, meta={'info': (prov, city, cur_url)})

    def parse_str(self, string):
        tmp = string.split("|")
        if len(tmp) == 3:
            level = tmp[0].split()[0].strip()
            room_type = tmp[0].split()[1].strip()
            area = tmp[1]
            orientations = tmp[2].strip()
            year = ''
            return level, year, room_type, area, orientations
        else:
            return '', '', '', '', ''
