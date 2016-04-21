# -*- coding: utf-8 -*-
import datetime
import re
import urlparse
import scrapy
from scrapy.selector import Selector
from selenium import webdriver
from time import sleep
from comment_scraper.items import CommentScraperItem


class DelfiSpider(scrapy.Spider):
    name = "delfi"

    def __init__(self, dfrom=None, dto=None, *args, **kwargs):
        super(DelfiSpider, self).__init__(*args, **kwargs)

        self.driver = webdriver.PhantomJS(service_args=['--load-images=false'])
        self.driver.set_window_size(1024, 768)

        if not dfrom or not dto:
            self.start_date = datetime.datetime.now().date()
            self.end_date = self.start_date
        else:
            self.start_date = datetime.datetime.strptime(dfrom, '%Y-%m-%d').date()
            self.end_date = datetime.datetime.strptime(dto, '%Y-%m-%d').date()
        self.step = datetime.timedelta(days=1)
        self.allowed_domains = ['delfi.lv']

        #Not working
        #https://github.com/scrapy/scrapy/issues/1343
        #self.custom_settings = {'CONCURRENT_REQUESTS': 5,
        #                        'RETRY_TIMES': 4,
        #                    }

        self.start_urls = (
            'http://www.delfi.lv/archive/?tod={2}-{1}-{0}&fromd={2}-{1}-{0}&channel=0&category=0&query=#'.format(
                str(self.start_date.year), str(self.start_date.month), str(self.start_date.day)),
            'http://rus.delfi.lv/archive/?tod={2}-{1}-{0}&fromd={2}-{1}-{0}&channel=0&category=0&query=#'.format(
                str(self.start_date.year), str(self.start_date.month), str(self.start_date.day)),
        )
        self.logger.info('\033[92m' + 'Datumu diapazons: %s - %s' + '\033[0m', self.start_date, self.end_date)

    def closed(self, reason):
        self.driver.quit()

    def parse(self, response):

        for article in response.xpath('//div[@class="arch-search-list"]/ol/li[@class="odd"]'):
            comment_url = article.xpath('div[@class="search-item-content"]/a[@class="commentCount"]/@href').extract()
            if comment_url:
                comment_url_unreg = re.sub('reg=1', 'reg=0', comment_url[0])
                for url in comment_url[0], comment_url_unreg:
                    yield scrapy.Request(url, callback=self.parse_comments)

        next_page = response.xpath('//a[@class="item next"]/@href').extract()
        if next_page:
            next_page = next_page[0].strip('\n\t')
            next_page = re.sub('\n\t+', '', next_page)
            yield scrapy.Request('http://' + urlparse.urlparse(response.url).netloc + next_page, callback=self.parse)
        else:  # TODO: fix date iteration
            self.start_date += self.step
            if self.start_date <= self.end_date:
                url = 'http://' + urlparse.urlparse(
                    response.url).netloc + '/archive/?tod={2}-{1}-{0}&fromd={2}-{1}-{0}&channel=0&category=0&query=#'.format(
                    str(self.start_date.year), str(self.start_date.month), str(self.start_date.day))

                yield scrapy.Request(url, callback=self.parse)

    def parse_comments(self, response):

        self.driver.get(response.url)

        try:
            yrscheck = self.driver.find_element_by_class_name("yrscheck-yes-input")
            if yrscheck:
                yrscheck.click()

        except:
            pass

        btns = self.driver.find_elements_by_class_name("load-more-comments-btn-link")
        url = self.driver.current_url
        i = 0
        while i < len(btns):
            i = 0
            for btn in btns:
                if btn.is_displayed():
                    btn.click()
                    sleep(0.5)
                else:
                    i += 1

        sel = Selector(text=self.driver.page_source)
        comment_count = sel.xpath('//div[@id="comments-list"]/@data-count').extract()[0]
        reg = sel.xpath('//div[contains( @class, "thread-switcher-selected-reg")]')
        anon = sel.xpath('//div[contains( @class, "thread-switcher-selected-anon")]')

        if int(comment_count) > 0:

            selxpath = 'None'
            if (anon and "reg=0" in url) or (reg and "reg=1" in url):
                if anon and "reg=0" in url:
                    selxpath = sel.xpath(
                        '//div[@id="comments-list"]//div[contains(@class, "comment-post") and not(contains(@class, "comment-deleted")) and not(contains(@class, "comment-avatar-registered"))]')

                elif reg and "reg=1" in url:
                    selxpath = sel.xpath(
                        '//div[@id="comments-list"]//div[contains(@class, "comment-post") and not(contains(@class, "comment-deleted")) and not(contains(@class, "comment-avatar-anonymous"))]')

                if selxpath != 'None':
                    for comment in selxpath:

                        item = CommentScraperItem()

                        if anon and "reg=0" in url:
                            comment_author = comment.xpath('div[@class="comment-author"]/text()').extract()[0].strip('\n\t')
                        elif reg and "reg=1" in url:
                            comment_author = comment.xpath('div[@class="comment-author"]/a/text()').extract()[0].strip('\n\t')
                        else:
                            comment_author = ''

                        comment_id = re.sub('[a-z]', '',
                                            comment.xpath('a[@class="comment-list-comment-anchor"]/@name').extract()[0])
                        date_time_str = comment.xpath('div[@class="comment-date"]/text()').extract()[0].strip('\n\t')
                        date_time = datetime.datetime.strptime(date_time_str, '%d.%m.%Y %H:%M')
                        comment_date = date_time.strftime('%Y-%m-%d')
                        comment_time = date_time.strftime('%H:%M:%S')
                        comment_txt = ''.join(comment.xpath(
                            'div[@class="comment-content"]/div[@class="comment-content-inner"]/text()').extract()).strip(
                            '\n\t')
                        recommend_pos = ''.join(comment.xpath(
                            'div[@class="comment-votes"]/div[@class="comment-votes-up"]/a/text()').extract()).strip('\n\t')
                        recommend_neg = ''.join(comment.xpath(
                            'div[@class="comment-votes"]/div[@class="comment-votes-down"]/a/text()').extract()).strip(
                            '\n\t')
                        if not recommend_neg and not recommend_pos:
                            recommend_neg = 0
                            recommend_pos = 0
                        article_id = re.search('(?<=id\=)(\d+)', url)
                        if not article_id:
                            article_id = re.search('(?<=\/)(\d+)', url).group()
                        else:
                            article_id = article_id.group()

                        item['article_id'] = article_id
                        item['comment_url'] = url
                        item['comment_txt'] = comment_txt
                        item['comment_date'] = comment_date
                        item['comment_time'] = comment_time
                        item['recommend_neg'] = int(recommend_neg)
                        item['recommend_pos'] = int(recommend_pos)
                        item['comment_author'] = comment_author
                        item['comment_id'] = comment_id

                        yield item

            next_page = sel.xpath('//a[@class="comments-pager-arrow-last"]/@href').extract()
            if next_page:
                yield scrapy.Request(next_page[0], callback=self.parse_comments)
