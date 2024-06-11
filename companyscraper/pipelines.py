# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from companyscraper.items import Client
import spacy


class CompanyscraperPipeline:

    nlp = spacy.load("en_core_web_sm")

    def process_item(self, item, spider):
        if isinstance(item, Client):
            companies = []
            names = []
            text = item["unprocessed_text_content"]
            doc = self.nlp(text)
            if doc.ents != []:
                for ent in doc.ents:
                    if (ent.label_ == "ORG"):
                        companies.append(ent.text)
                    if (ent.label_ == "PERSON"):
                        names.append(ent.text)
                item["company"] = companies
                item["name"] = names
                item["text_content"] = "Here's the text where this client was found: " + text
        
        return item

