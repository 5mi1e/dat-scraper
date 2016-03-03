# -*- coding: utf-8 -*-
import scrapy
import datetime
import re
import json
from scrapy.selector import Selector
from comment_scraper.items import CommentScraperItem

class DelfiSpider(scrapy.Spider):
    name = "delfi"
    script="""
        function main(splash)
            splash.images_enabled = false
            assert(splash:autoload("https://code.jquery.com/jquery-2.1.3.min.js"))
            assert(splash:go(splash.args.url))
            local show_c = splash:jsfunc([[
                function showComments(){
                var shown = document.querySelectorAll('div.load-more-comments-btn[style="display: none;"]').length
                var hidden = document.querySelectorAll('div.load-more-comments-btn').length
                    var divs = document.querySelectorAll('div.load-more-comments-btn'), i;
                    for (i = 0; i < divs.length; ++i) {
                            if ((divs[i].style.display) != "none"){
                                $(divs[i].querySelector("a.load-more-comments-btn-link").click());
                            }
                    }
                setTimeout(function(){
                    shown = document.querySelectorAll('div.load-more-comments-btn[style="display: none;"]').length
                        if (shown < hidden) {
                            showComments();
                        }
                    }, 500)
                }
            ]])
        show_c()
        assert(splash:wait(7.0))
        return {
            html = splash:html(),
            url = splash.args.url,
            }


        end
    """
    def __init__(self, dfrom=None, dto=None, *args, **kwargs):
        super(DelfiSpider, self).__init__(*args, **kwargs)
        if not dfrom or not dto:
            self.start_date = datetime.datetime.now().date()
            self.end_date = self.start_date
        else:
            self.start_date = datetime.datetime.strptime(dfrom, '%Y-%m-%d').date()
            self.end_date = datetime.datetime.strptime(dto, '%Y-%m-%d').date()
        self.step = datetime.timedelta(days=1)
        self.allowed_domains = ['delfi.lv']
        self.start_urls = (
            'http://www.delfi.lv/archive/?tod={2}-{1}-{0}&fromd={2}-{1}-{0}&channel=0&category=0&query=#'.format(
                str(self.start_date.year), str(self.start_date.month),str(self.start_date.day)),
        )
        self.logger.info('\033[92m' + 'Datumu diapazons: %s - %s' + '\033[0m', self.start_date, self.end_date)

    def parse(self, response):
        for article in response.xpath('//div[@class="arch-search-list"]/ol/li[@class="odd"]'):
            comment_url = article.xpath('div[@class="search-item-content"]/a[@class="commentCount"]/@href').extract()
            if comment_url:
                comment_url_unreg = re.sub('reg=1', 'reg=0', comment_url[0])
                for url in comment_url[0], comment_url_unreg:
                    yield scrapy.Request(url, callback=self.parse_comments,meta={
                        'splash':{
                            'args':{'lua_source': self.script,},
                            'endpoint':'execute',
                        }
                    })
        next_page = response.xpath('//a[@class="item next"]/@href').extract()
        if next_page:
            next_page = next_page[0].strip('\n\t')
            next_page = re.sub('\n\t+', '', next_page)
            yield scrapy.Request('http://www.delfi.lv' + next_page, callback=self.parse)


    def parse_comments(self, response):
        data = json.loads(response.body_as_unicode())
        url = data['url']
        sel = Selector(text=data['html'])

        #from scrapy.shell import inspect_response
        #inspect_response(response, self)

        comment_count = sel.xpath('//div[@id="comments-list"]/@data-count').extract()[0]
        reg  = sel.xpath('//div[contains( @class, "thread-switcher-selected-reg")]')
        anon = sel.xpath('//div[contains( @class, "thread-switcher-selected-anon")]')


        if int(comment_count) > 0:

            item = CommentScraperItem()
            if anon and "reg=0" in url:
                for comment in sel.xpath('//div[@id="comments-list"]//div[contains(@class, "comment-post")]'):
                    if not comment.xpath('div[@class="comment-author"]/a') and not comment.re('comment-deleted'):
                        try:
                            comment_author = comment.xpath('div[@class="comment-author"]/text()').extract()[0].strip('\n\t')
                            item['comment_author'] = comment_author
                        except:
                            self.logger.info(url)
            elif reg and "reg=1" in url:
                for comment in sel.xpath('//div[@id="comments-list"]//div[contains(@class, "comment-post")]'):
                    if not comment.re('comment-deleted'):
                        try:
                            comment_author = comment.xpath('div[@class="comment-author"]/a/text()').extract()[0].strip('\n\t')
                            item['comment_author'] = comment_author
                        except:
                            print comment.xpath('div[@class="comment-author"]/text()').extract()[0].strip('\n\t')
                            self.logger.info(url)

            next_page = sel.xpath('//a[@class="comments-pager-arrow-last"]/@href').extract()
            if next_page:
                yield scrapy.Request(next_page[0], callback=self.parse_comments,meta={
                    'splash':{
                        'args':{'lua_source': self.script,},
                        'endpoint':'execute',
                    }
                })
            yield item