# -*- coding: utf-8 -*-
import scrapy


class DelfiSpider(scrapy.Spider):
    name = "delfi"
    allowed_domains = ["delfi.lv"]
    start_urls = (
        'http://www.delfi.lv/',
    )

    def parse(self, response):
        pass

#http://www.delfi.lv/archive/?tod=12.02.2016&fromd=12.02.2016&channel=0&category=0&query=#