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




class SitespiderSpider(CrawlSpider):
    name = "sitespider"
    allowed_domains = ["slalom.com"]
    start_urls = ["https://slalom.com/us/en"]
    #Define rules for crawling
    rules = (Rule(LinkExtractor(allow=('(/us/en)(.)*$')), callback='parse_item', follow=False),)

    def __init__(self, *args, **kwargs):
        super(SitespiderSpider, self).__init__(*args, **kwargs)
        self.nlp = spacy.load("en_core_web_sm") #load the pipeline/model

    def parse_item(self, response): #response comes from request
        try:
            url = response.url
            # Use Beautiful soup to parse the response body with html.parser. Want any information that has to do with client companies
            soup = BeautifulSoup(response.body, "html.parser")
            section_classes = []
            carousel_classes = []
    
            for section in soup.find_all("section"): #check for sections with ex "cmp-container" in class list?
                class_list = section.get("class")
                section_classes.append(class_list)
                carousels = section.find_all(attrs={"aria-label": "carousel"})
                for carousel in carousels:
                    carousel_classes.append(carousel.get("class"))
            
            print(len(carousel_classes))
            print(carousel_classes)

                #slides = section.find_all("div", {"class": "slick-slide"})
                #slides = section.xpath('//div[@class="slick-slide"]')
                #print(len(slides))
    
            '''for slide in slides: #each slide tends to correspond to one client
                    print(slide)
                    client = Client()
                    client.web_page_url = url
                    text = slide.get_text().strip
                    #print(text)
                    doc = self.nlp(text) #create the tokenized and annotated doc, for each slide
                    for ent in doc.ents: #iterating through each named, "real-world" token in the doc
                        if (ent.label_ == "ORG"): #Type for the entity is either an Organization or Person
                            client.company = ent.label_
                        elif (ent.label_ == "PERSON"):
                            client.name = ent.label_
                    for sentence in doc.sents:
                        if any(keyword in sentence.text.lower() for keyword in ["said", "mentioned", "commented"]):
                            client.text_content = sentence.text
                    client.text_content = text
                    yield client'''

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
