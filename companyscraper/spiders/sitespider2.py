import scrapy
from bs4 import BeautifulSoup
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request
from scrapy.utils.response import response_status_message
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError
from scrapy.spidermiddlewares.httperror import HttpError
import spacy
from companyscraper.items import Client
import lxml




class Sitespider2Spider(scrapy.Spider):
    name = "sitespider2"
    allowed_domains = ["slalom.com"]
    start_urls = ["https://slalom.com/us/en"]
    rules = (Rule(LinkExtractor(allow=('(/us/en)(.)*$')), callback='parse_item', follow=True),)
        #need to fix the above regular expression

    def __init__(self, *args, **kwargs):
        super(Sitespider2Spider, self).__init__(*args, **kwargs)
    
    '''def defines_class(tag):
        return tag.has_attr("class")'''

    def parse_item(self, response):
        try:
            url = response.url

            soup = BeautifulSoup(response.body, "html.parser")
            body = soup.find("body")

            page_text = response.css("body::text").get()
            paragraphs = response.css("p::text").getall()
            h1s = []
            h2s = []
            h3s = []
            h4s = []
            h5s = []
            h6s = []
            lists = []
            list_items = []
            links = []
            #page_text = body.get_text()
            
            string = ""
            for sentence in page_text:
                for i in range(0, len(sentence), 1):
                    if (sentence[i] != "\n"):
                        string = string + sentence[i]
            #print(string)

            #string = string.split(" ")
            string = string.split(".")
            #print(string)

            size = len(string)
            for i in range(0, size-2, 3):
                client = Client()
                client["web_page_url"] = url
                text = string[i] + string[i+1] + string[i+2]
                client["unprocessed_text_content"] = text
                yield client


            
            '''page_text = page_text.replace("\n", "" )
            print(type(page_text))
            page_text.split("|")
            for text in page_text:
                if text != "|":
                    page_text_updated.append(text)'''
            
            #div_list = soup.find_all("div")
            '''for div in div_list:
                if (div.get_text() != ""):
                    div_text.append(div.get_text())
                    divs.append(div.prettify())''' 
                #if div.has_attr("aria-label"):
                    #div_elements.append(div)
        
            '''for div in div_list:
                descendants = div.descendants
                for descendant in descendants:
                    if descendant.name in ["h1", "h2", "h3", "p"]:
                        if descendant.string'''

        except AttributeError as e:       
            self.logger.error(f"Failed to parse item on {response.url}: {e}")




    def handle_error(self, failure): #failure is the response when an error occurs
        # Log all failures
        self.logger.error(repr(failure)) 

        if failure.check(HttpError):
            # Get the response
            response = failure.value.response
            self.logger.error(f"HttpError on {response.url}")

        elif failure.check(DNSLookupError):
            #This is the original request
            request = failure.request
            self.logger.error(f"DNSLookupError on {request.url}")

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error(f"TimeoutError on {request.url}")

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse_item, errback=self.handle_error)

           

            
