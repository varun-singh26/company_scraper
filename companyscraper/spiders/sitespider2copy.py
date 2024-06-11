
import sys
import scrapy
from bs4 import BeautifulSoup, Tag
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request
from scrapy.utils.response import response_status_message
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.loader import ItemLoader
import spacy
import spacy_transformers
from companyscraper.items import Client
import lxml

#sys.setrecursionlimit(100)
class Sitespider2copySpider(CrawlSpider):
    name = "sitespider2copy"
    allowed_domains = ["slalom.com"] #["konrad.com"]
    start_urls = ["https://slalom.com/us/en"] #["https://www.konrad.com"]
    rules = (
       Rule(LinkExtractor(allow=(r"/us/en.*"), allow_domains=('slalom.com',), deny_domains=('jobs.slalom.com',),), callback='parse_item', follow=True),
    )
    client_list = []
    nlp = spacy.load("en_core_web_trf") 

    custom_settings = {
        "CLOSESPIDER_PAGECOUNT": 20
    }
  

    @staticmethod
    def find_all_tags(body):
        all_tags = []
        tags = ["h1", "h2", "h3", "h4", "h5", "h6",]
        for tag in tags:
            elements = body.find_all(tag)
            all_tags = all_tags + elements
        return all_tags
    
    @staticmethod
    def client_already_exists(type, text, client_list):
        if type == "PERSON":
            for client in client_list:
                if text in client["representatives"] or text in client["context"]: #If the client's context contains the passed text,
                    return (True, client)                                           # it likely is the desired client
            return (False, None)
        
        elif type == "ORG":
            for client in client_list:
                if text in client["company"] or text in client["context"]:#If the client's context contains the passed text,
                    return (True, client)                                           # it likely is the desired client
            return (False, None)
        
        return False, None
    
    @staticmethod
    def get_siblings(tag):
        all_siblings = []
        previous_siblings = tag.previous_siblings
        next_siblings = tag.next_siblings
        for sibling in previous_siblings:
            all_siblings.append(sibling)
        for sibling in next_siblings:
            all_siblings.append(sibling)
        return all_siblings #list of HTML elements
    
    @staticmethod
    def create_initialize_client():
        client = Client()
        client["representatives"] = []
        client["company"] = []
        client["context"] = []
        client["web_page_url"] = ""
        return client
    
    @staticmethod
    def organize_information(client, all_siblings, nlp): #You have all the siblings, it's about organizing where each 
                                                        # of their information goes for the client
        if all_siblings: #[h1, h2, h3, h4, h5, h6, p, div, a, li, ul]
            for sibling in all_siblings:
                if isinstance(sibling, Tag):
                    if sibling.name in ["p", "div", "span", "i", "li"]: #Add more context to that client
                        if sibling.text not in client["context"]: #avoid adding duplicate information to client object attributes
                            client["context"].append(sibling.text)

                    if sibling.name in ["h1", "h2", "h3", "h4", "h5", "h6", "a"]: #Probably going to be a Person or an Org,
                        text = sibling.text
                        doc = nlp(text)
                        if any(entity for entity in doc.ents if entity.label_ == "PERSON"):
                            if sibling.text not in client["representatives"]:
                                client["representatives"].append(text)

                        elif any(entity for entity in doc.ents if entity.label_ == "ORG"):
                            if sibling.text not in client["company"]:
                                client["company"].append(text)
                    #elif sibling.name in ["div", "h1", "h2", "h3", "h4", "h5"]:
                    '''if sibling.contents: #any tag w children
                        Sitespider2copySpider.find_context(client, sibling.contents, nlp)''' #Sometimes the context, Person, Org, lies in the children
                                    
                            
    def parse_item(self, response):
        #l = ItemLoader(item=Client(), response=response)

        #dummy_client = self.create_initialize_client()
        #client_list.append(dummy_client)
        url = response.url
        self.logger.info(f"Processing URL: {url}")

        
        try:
            soup = BeautifulSoup(response.body, "html.parser")
            body = soup.find("body")

            

            tags = self.find_all_tags(body)

            for tag in tags: #["h1", "h2", "h3", "h4", "h5", "h6",] , for li we don't want to search siblings (in list, siblings will refer to different clients)
                doc = self.nlp(tag.get_text(separator="", strip=True))
                if doc.ents:
                    for entity in doc.ents:
                        if entity.label_ == "PERSON" or entity.label_ == "ORG":
                            exists, client = self.client_already_exists(entity.label_, entity.text, self.client_list) 
                            if exists:
                                all_siblings = self.get_siblings(tag) #more information on this client will be located in tags that are siblings of the searched tag
                                self.organize_information(client, all_siblings, self.nlp)
  
                            else:
                                client = self.create_initialize_client()
                                client["web_page_url"] = url
                                if entity.label_ == "PERSON":
                                    client["representatives"].append(entity.text)
                                elif entity.label_ == "ORG":
                                    client["company"].append(entity.text)
                                all_siblings = self.get_siblings(tag) #list of HTML elements
                                self.organize_information(client, all_siblings, self.nlp)
                                self.client_list.append(client)
                                
                        else:
                            pass

                else:
                    pass

            #self.logger.info(f"Found {len(client_list)} clients on {url}")
            


        except AttributeError as e:
            self.logger.error(f"Failed to parse item on {response.url}: {e}")
        
        self.logger.info(f"{len(self.client_list)}")


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



    def closed(self, reason): #By making it an instance method, this method can 
                                # access all the attributes of this instance of Sitespider2copySpider 
    #print each client in final client list
        self.logger.info(f"Spider closed: {reason}")
        for client in self.client_list:
            print(f"Client: {client['company']}")
            print(f"Client representatives: {client['representatives']}")
            print(f"Client Context: {client['context']}")
            print(f"Client was mentioned on these urls: {client['web_page_url']}")
            print("---------")






