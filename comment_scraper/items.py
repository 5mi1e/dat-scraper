# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class CommentScraperItem(Item):
    article_id = Field()
    comment_author = Field()
    comment_id = Field()
    comment_txt = Field()
    comment_date = Field()
    comment_time = Field() #?
    recommend_pos = Field()
    recommend_neg = Field()
    comment_url = Field()
    author_auth = Field()
    top100 = Field()
