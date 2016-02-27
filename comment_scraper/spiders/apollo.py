# -*- coding: utf-8 -*-

import re
import datetime
import urllib
import dateutil.parser
import scrapy

from comment_scraper.items import CommentScraperItem


class ApolloSpider(scrapy.Spider):
    name = "apollo"

    def __init__(self, dfrom=None, dto=None, *args, **kwargs):
        super(ApolloSpider, self).__init__(*args, **kwargs)
        if not dfrom or not dto:
            self.start_date = datetime.datetime.now().date()
            self.end_date = self.start_date
        else:
            self.start_date = datetime.datetime.strptime(dfrom, '%Y-%m-%d').date()
            self.end_date = datetime.datetime.strptime(dto, '%Y-%m-%d').date()
        self.step = datetime.timedelta(days=1)
        self.allowed_domains = ['apollo.tvnet.lv']
        self.start_urls = (
            'http://apollo.tvnet.lv/arhivs/{0}/{1}/{2}'.format(str(self.start_date.year), str(self.start_date.month),
                                                               str(self.start_date.day)),
        )
        self.logger.info('\033[92m' + 'Datumu diapazons: %s - %s' + '\033[0m', self.start_date, self.end_date)

    def parse(self, response):
        for article in response.xpath(
                '//div[@class="items"]/article[@class="article-medium"]//h2[@class="article-title"]'):
            comment_url = article.xpath('a[@class="article-comments-count"]/@href').extract()
            if comment_url:
                comment_count = int(re.search('([0-9])', str(
                    article.xpath('a[@class="article-comments-count"]/span/text()').extract())).group())
                if comment_count > 0:
                    yield scrapy.Request(comment_url[0], callback=self.parse_comments)
        self.start_date += self.step
        if self.start_date <= self.end_date:
            url = 'http://apollo.tvnet.lv/arhivs/' + str(self.start_date.year) + '/' + str(
                self.start_date.month) + '/' + str(self.start_date.day)
            yield scrapy.Request(url, self.parse)

    def parse_comments(self, response):
        for comment in response.xpath('//div[@class="article-comments"]/div[ contains(@class, "article-comment")]'):
            if not comment.xpath('p[@class="no-comments-alert"]'):
                item = CommentScraperItem()
                item['article_id'] = re.search('(?<=\/)\d{4,10}', response.url).group() # TODO: Test this
                item['comment_id'] = re.search('([0-9]+)', comment.xpath('@id').extract()[0]).group()
                auth = comment.xpath(
                    'div/span[@class="article-comment-pic"]//span[contains(@class, "icon-soc")]/@title').extract()
                if auth:
                    item['author_auth'] = auth[0]
                item['comment_author'] = ''.join(
                    comment.xpath('div/span[@class="article-comment-pic"]/img/@title').extract())
                date = dateutil.parser.parse(''.join(comment.xpath('div/time/@datetime').extract()))
                item['comment_date'] = datetime.datetime.strftime(date, '%Y-%m-%d')
                item['comment_time'] = datetime.datetime.strftime(date, '%H:%M:%S')
                pos = comment.xpath('div/div/div/div/a[ contains(@class, "plus") ]/text()').extract()
                if pos:
                    item['recommend_pos'] = int(pos[0])
                neg = comment.xpath('div/div/div/div/a[ contains(@class, "minus") ]/text()').extract()
                if neg:
                    item['recommend_neg'] = int(neg[0])

                item['comment_url'] = response.url
                comment_txt = comment.xpath(
                    'div[@class="article-comment-content"]/text() | div[@class="article-comment-content"]/a/@href'
                    ).extract()
                comment_txt = ' '.join(comment_txt)
                if "/comment/external" in comment_txt:
                    comment_txt = re.sub('(/comment/external.url=)', "", comment_txt)
                    comment_txt = re.sub('(&hash=[a-z0-9]*)', "", comment_txt)
                    comment_txt = urllib.unquote(comment_txt)
                item['comment_txt'] = comment_txt
                yield item
        next_page = response.xpath('//a[@class="pageing-button-next"]/@href').extract()
        if next_page:
            yield scrapy.Request('http://apollo.tvnet.lv' + ''.join(next_page), callback=self.parse_comments)
