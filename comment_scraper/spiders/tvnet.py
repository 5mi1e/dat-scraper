# -*- coding: utf-8 -*-
import scrapy


class TvnetSpider(scrapy.Spider):
    name = "tvnet"
    allowed_domains = ["tvnet.lv"]
    start_urls = (
        'http://www.tvnet.lv/',
    )

    def parse(self, response):
        pass
