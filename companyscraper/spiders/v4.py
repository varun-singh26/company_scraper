import sys
import scrapy
from bs4 import BeautifulSoup, Tag, NavigableString
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


class V4Spider(CrawlSpider):
    name = "v4"
    allowed_domains = ["www.ltimindtree.com", "www.hcltech.com", "www.persistent.com", "www.konrad.com", "www.slalom.com", "www.cognizant.com", "www.perficient.com", "www.accenture.com", "www.infosys.com"] #"www.linkedin.com"
    start_urls = ["https://www.ltimindtree.com", "https://www.hcltech.com", "https://www.accenture.com/us-en", "https://www.slalom.com/us/en", "https://www.persistent.com", "https://www.cognizant.com/us/en", "https://www.infosys.com", "https://www.perficient.com"] # "https://www.cognizant.com/us/en" "https://www.linkedin.com/in/tylerschulze/  "https://www.slalom.com/us/en" "https://www.cognizant.com/us/en/industries/life-sciences-technology-solutions"

    rules = (
        # Follow all links within the same domain
        Rule(LinkExtractor(allow=(r"/us/en.*"), allow_domains=("www.slalom.com", "www.cognizant.com",), deny_domains=('jobs.slalom.com',),), callback='parse_item', follow=True),
        Rule(LinkExtractor(allow=(r"/.*"), allow_domains=("www.perficient.com", "www.persistent.com", "www.infosys.com", "www.hcltech.com", "www.ltimindtree.com"),), callback='parse_item', follow=True),
        Rule(LinkExtractor(allow=(r"/us-en/.*"), allow_domains=("www.accenture.com",),), callback='parse_item', follow=True)


    )

    client_list = []
    nlp = spacy.load("en_core_web_trf") 

    '''custom_settings = {
        "CLOSESPIDER_PAGECOUNT": 100
    }'''
    
    def parse_item(self, response):
    
        url = response.url
        self.logger.info(f"Processing URL: {url}")

        
        try:
            soup = BeautifulSoup(response.body, "html.parser")
            body = soup.find("body")
            tags = self.find_all_tags(body)

            '''additional_tags = body.find_all('div', class_='client-info')
            additional_tags += body.find_all('div', attrs={'data-client-section': 'true'})
            tags.extend(additional_tags)'''


            for tag in tags: #["h1", "h2", "h3", "h4", "h5", "h6",] , for li we don't want to search siblings (in list, siblings will refer to different clients)
                doc = self.nlp(tag.get_text(separator="", strip=True))
                if doc.ents:
                    for entity in doc.ents:
                        if entity.label_ == "PERSON" or entity.label_ == "ORG":
                            exists, client = self.client_already_exists(entity.label_, entity.text, self.client_list) 
                            if not exists:
                                client = self.create_initialize_client()
                                client["web_page_url"] = url
                                if entity.label_ == "PERSON":
                                    client["representatives"].append(entity.text)
                                elif entity.label_ == "ORG":
                                    client["company"].append(entity.text)
                                self.client_list.append(client)
                            
                            self.organize_information(client, tag, self.nlp)
                                
                        else:
                            pass

                else:
                    pass 

        except AttributeError as e:
            self.logger.error(f"Failed to parse item on {response.url}: {e}")
        
        self.logger.info(f"{len(self.client_list)}")     

    
    

    def organize_information(self, client, element, nlp):
        # Check immediate siblings
        self.extract_info_from_siblings(client, element, nlp)
        if self.is_info_sufficient(client):
            return

        # Check parent element and its siblings
        '''self.extract_info_from_parent(client, element, nlp)'''
        
        return
        

    def is_info_sufficient(self, client):
        # Define your criteria for sufficient information
        if not client["representatives"] or not client["company"]:
            return False

        context_text = " ".join(client["context"])
        if len(context_text) < 50 or len(client["context"]) < 3:
            return False
        
        return True
    
    def extract_info_from_siblings(self, client, element, nlp):
        all_siblings = self.get_siblings(element) #don't want to extract the text from the start element,
                                                    #because that will already be included in the "representatives"
                                                    #or "company" fields for the client
        
        self.extract_info_from_elements(client, all_siblings, nlp) #search sibling tags, and children of sibling tags

    
    
    
    
    
    def extract_info_from_parent(self, client, element, nlp):
        parent = element.parent
        if parent and isinstance(parent, Tag):
            parent_siblings = self.get_siblings(parent)
            parent_and_siblings = [parent] + parent_siblings
            self.extract_info_from_elements(client, parent_and_siblings, nlp) #search parent tag, all cousins and their children/children's children

    # Note: extract_info_from_children is not needed since get_text_recursive handles descendant text extraction



    def extract_info_from_elements(self, client, elements, nlp):
        for element in elements:
            if isinstance(element, Tag):
                text = self.get_text_recursive(element)
                if text:
                    doc = nlp(text)  
                    for entity in doc.ents: #Going to get a lot of client objects with "Slalom" in one of their fields
                        if entity.label_ == "PERSON" and entity.text not in client["representatives"]:
                            client["representatives"].append(entity.text)
                        elif entity.label_ == "ORG" and entity.text not in client["company"]:
                            client["company"].append(entity.text)
                    if text not in client["context"]:
                        client["context"].append(text)

    
    @staticmethod
    def get_text_recursive(tag):
        if isinstance(tag, NavigableString): #Navigable String is a piece of text 
            return tag.strip()               #in the Beautiful Soup Parse Tree
        elif isinstance(tag, Tag):
            parts = [V4Spider.get_text_recursive(child) for child in tag.children]
            return " ".join(filter(None, parts)).strip()
        return ""


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

    '''def handle_error(self, failure): #failure is the response when an error occurs
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
            self.logger.error(f"TimeoutError on {request.url}")'''

    def closed(self, reason): #By making it an instance method, this method can 
                                # access all the attributes of this instance of Sitespider2copySpider 
    #print each client in final client list
        self.logger.info(f"Spider closed: {reason}")
        for client in self.client_list:
            context_text = " ".join(client["context"])
            if len(context_text) > 100:
                self.client_list.remove(client)
        
        for 
            print(f"Client: {client['company']}")
            print(f"Client representatives: {client['representatives']}")
            print(f"Client Context: {client['context']}")
            print(f"Client was mentioned on these urls: {client['web_page_url']}")
            print("---------")
