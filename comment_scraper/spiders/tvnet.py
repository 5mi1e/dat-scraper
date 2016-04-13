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
                yield scrapy.Request(comments_url[0], callback=self.parse_comments)
        self.start_date += self.step
        if self.start_date <= self.end_date:
            url = 'http://www.tvnet.lv/archive/all/' + self.start_date.strftime('%Y-%m-%d')
            url_rus = 'http://rus.tvnet.lv/archive/all/' + self.start_date.strftime('%Y-%m-%d')
            yield scrapy.Request(url, callback=self.parse)
            yield scrapy.Request(url_rus, callback=self.parse)

    def parse_comments(self, response):
        if response.xpath('//ol[@class="commentary"]/li/div[@class="comment-container"]'):
            for comment in response.xpath('//ol[@class="commentary"]/li'):
                if comment.xpath('div[@class="comment-container"]'):
                    item = CommentScraperItem()
                    article_id = re.search('(?<=\/)([0-9]*)(?=\-)', response.url).group()
                    item['article_id'] = article_id
                    date_time = self.string_to_datetime(''.join(comment.xpath('div[@class="comment-container"]/div/span[@class="date"]/a/text()').extract()))
                    item['comment_date'] = date_time.strftime('%Y-%m-%d')
                    item['comment_time'] = date_time.strftime('%H:%M:%S')

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
            next_page = response.xpath('//a[contains(@class, "next")]/@href').extract()
            if next_page and next_page[0] != "#":
                yield scrapy.Request(next_page[0], callback= self.parse_comments)

    def string_to_datetime(self, dstring):
        commentDT = datetime.time(0, 0)
        if u"Šodien" in dstring or u"Vakar" in dstring or u"Сегодня" in dstring or u"Вчера" in dstring:
            commentTime = datetime.datetime.strptime(re.search('\d.:\d.', dstring).group(), '%H:%M').time()
            if u"Vakar" in dstring or u"Вчера" in dstring:
                delta=1
            else:
                delta=0
            commentDT = datetime.datetime.combine(datetime.date.today(), commentTime) - datetime.timedelta(days=delta)
        elif u"Pirms" in dstring or u"ч." in dstring or u"мин." in dstring or u"сек." in dstring:
            h=0
            m=0
            s=0
            if "stund" in dstring:
                h = re.search('\d+(?=\sstun)', dstring).group()
            if u"ч." in dstring:
                h = re.search(u'\d+(?=\sч\.)', dstring, re.U).group()
            if "min" in dstring:
                m = re.search('\d+(?=\smin)', dstring).group()
            if u"мин." in dstring:
                m = re.search(u'\d+(?=\sмин\.)', dstring, re.U).group()
            if "sekund" in dstring:
                s = re.search('\d+(?=\ssek)', dstring).group()
            if u"сек." in dstring:
                s = re.search(u'\d+(?=\sсек\.)', dstring, re.U).group()
            commentDT = datetime.datetime.combine(datetime.date.today(), datetime.datetime.now().time()) - datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s))
        else:
            if dstring:
                if re.search(u'[а-яА-Я]', dstring, re.U):
                    year = re.search(u'\d+(?=\sг\.)', dstring, re.U).group()
                    month_string = re.search( u'\w+(?=\s\d{4})', dstring, re.U).group()
                    day = re.search( '^\d+',dstring).group()
                    time = re.search( '\d.:\d.',dstring).group()
                    m = {u'января': 1, u'февраля': 2, u'марта': 3, u'апреля':4, u'мая':5, u'июня':6, u'июля':7, u'августа':8, u'сентября':9, u'октября':10, u'ноября':11, u'декабря':12}
                else:
                    year = re.search('\d+(?=.\sg)', dstring).group()
                    month_string = re.search( '\w+(?=\s\d.:\d.)', dstring, re.U).group()
                    day = re.search( '(?<=g.\s)\d+',dstring).group()
                    time = re.search( '\d.:\d.',dstring).group()
                    m = {u'janvārī': 1, u'februārī': 2, u'martā': 3, u'aprīlī':4, u'maijā':5, u'jūnijā':6, u'jūlijā':7, u'augustā':8, u'septembrī':9, u'oktobrī':10, u'novembrī':11, u'decembrī':12}
                month_num = m[month_string]
                date_s = str(year)+'-'+str(month_num)+'-'+str(day)
                commentDT = datetime.datetime.strptime(date_s+' '+time, '%Y-%m-%d %H:%M')
        return commentDT
