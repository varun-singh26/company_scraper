# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Client(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    representatives = scrapy.Field()
    company = scrapy.Field() 
    context = scrapy.Field()
    web_page_url = scrapy.Field()
    ID = scrapy.Field()
   
    
    
    

