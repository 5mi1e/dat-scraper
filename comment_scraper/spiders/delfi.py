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
