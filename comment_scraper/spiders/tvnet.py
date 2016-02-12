# -*- coding: utf-8 -*-
import datetime
import re

import scrapy

from comment_scraper.items import CommentScraperItem


class TvnetSpider(scrapy.Spider):
    name = "tvnet"

    def __init__(self, dfrom=None, dto=None, *args, **kwargs):
        super(TvnetSpider, self).__init__(*args, **kwargs)
        if not dfrom or not dto:
            self.start_date = datetime.datetime.now().date()
            self.end_date = self.start_date
        else:
            self.start_date = datetime.datetime.strptime(dfrom, '%Y-%m-%d').date()
            self.end_date = datetime.datetime.strptime(dto, '%Y-%m-%d').date()
        self.step = datetime.timedelta(days=1)
        self.allowed_domains = ['tvnet.lv']
        self.start_urls = (
            'http://www.tvnet.lv/archive/all/' + self.start_date.strftime('%Y-%m-%d'),
            'http://rus.tvnet.lv/archive/all/' + self.start_date.strftime('%Y-%m-%d'),
        )
        self.logger.info('\033[92m' + 'Datumu diapazons: %s - %s' + '\033[0m', self.start_date, self.end_date)

    def parse(self, response):
        for article in response.xpath('//div[ contains(@class, "list highlight late") ]/ul/li/div/h4'):
            comments_url = article.xpath('a[@class="comment"]/@href').extract()
            if comments_url:
                d_current = re.search('(?<=all\/)(.*$)', response.url).group()
                yield scrapy.Request(comments_url[0], callback=lambda r, date=d_current: self.parse_comments(r, date))
        self.start_date += self.step
        if self.start_date <= self.end_date:
            url = 'http://www.tvnet.lv/archive/all/' + self.start_date.strftime('%Y-%m-%d')
            url_rus = 'http://rus.tvnet.lv/archive/all/' + self.start_date.strftime('%Y-%m-%d')
            yield scrapy.Request(url, callback=self.parse)
            yield scrapy.Request(url_rus, callback=self.parse)

    def parse_comments(self, response, date):
        if response.xpath(
                '//ol[@class="commentary"]/li/div[@class="comment-container"]/div/div[@class="comment-tool-container"]//@data-comment-id').extract():
            for comment in response.xpath('//ol[@class="commentary"]/li'):
                try:
                    item = CommentScraperItem()
                    article_id = re.search('(?<=\/)([0-9]*)(?=\-)', response.url).group()  # for md5?
                    item['article_id'] = article_id
                    item['comment_date'] = date
                    item['comment_id'] = comment.xpath('div[@class="comment-container"]/div/div[@class="comment-tool-container"]//@data-comment-id').extract()[0]
                    comment_author = comment.css('span.author::text').extract()
                    if comment_author:
                        comment_author = map(unicode.strip, comment_author)
                        comment_author = ''.join(comment_author)
                        item['comment_author'] = comment_author
                    item['recommend_pos'] = int(comment.xpath(
                        'div[@class="comment-container"]/div/div[@class="comment-tool-container"]//div[@class="recommend-count"]/text()').extract()[
                                                    0])
                    comment_txt = comment.xpath(
                        'div[@class="comment-container"]/p[@class="message"]/text() | div[@class="comment-container"]/p[@class="message"]/a/@href').extract()
                    if comment_txt:
                        item['comment_txt'] = ' '.join(comment_txt)
                    item['comment_url'] = ''.join(comment.xpath(
                        'div[@class="comment-container"]/div/span[@class="date"]/a/@href').extract())
                    avatar = comment.xpath('div[@class="author-picture-container"]/img/@src').extract()
                    author_auth = comment.xpath(
                        'div[@class="comment-container"]/div/span[@class="author"]/img/@src').extract()
                    if re.search('(?<=icon)([a-zA-Z]*)(?=\.)', str(avatar)):
                        if re.search('(?<=icon)([a-zA-Z]*)(?=\.)', str(avatar)).group() == "TvnetBig":
                            item['author_auth'] = "Tvnet"
                    else:
                        if author_auth:
                            if len(author_auth) > 1:
                                author_auth = re.search('(?<=icon)([a-zA-Z]*)(?=\.)', str(author_auth[1])).group()
                            else:
                                author_auth = re.search('(?<=icon)([a-zA-Z]*)(?=\.)', str(author_auth)).group()
                            item['author_auth'] = author_auth
                    if comment.xpath(
                            'div[@class="comment-container"]/div/span[@class="author"]/img[@class="top-commentator"]'):
                        item['top100'] = 1
                    yield item
                except:
                    pass
            next_page = response.xpath('//a[contains(@class, "next")]/@href').extract()
            if next_page and next_page[0] != "#":
                yield scrapy.Request(next_page[0], callback=lambda r, date=date: self.parse_comments(r, date))
