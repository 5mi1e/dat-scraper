# -*- coding: utf-8 -*-
import scrapy


class ApolloSpider(scrapy.Spider):
    name = "apollo"
    allowed_domains = ["apollo.tvnet.lv"]
    start_urls = (
        'http://apollo.tvnet.lv/',
    )

    def parse(self, response):
        pass
