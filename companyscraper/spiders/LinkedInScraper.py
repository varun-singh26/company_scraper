'''if domain == "www.linkedin.com":   #Want to get profile information (about me, work experience, etc.)
                profile = self.create_initialize_item("profile")
                about_sec = body.find("div", {"class" : "tYLAgXXELrpPTQckISFFNZgRhcumLDKI"}) #class attribute is 
                for section in about_sec.descendants:                                        #used in the experience section too
                    about_me = section.get_text(separator="", strip=True)
                    if about_me not in profile["about_me"]:
                        profile["about_me"].append(about_me)

                experience_list = body.find("ul", {"class" : "BwnTNCnDaJyEVotvulFBRVHudXozmSiNBUE"}).children
                
                for list_item in experience_list:
                    experience_header = list_item.find("div", {"class" : "display-flex" "flex-column" "full-width"}).get_text
                    doc = self.nlp(experience_header)
                    for entity in doc.ents:
                        if entity.label_ == "ORG":
                            profile["company"].append(entity.text)
                        if entity.label_ == "GPE":
                            profile["location"].append(entity.text)
                    experience_information = list_item.find_all("li", {"class" : "ECrgjsOASOamFiXcCSClYpcgUBSwwkLfGsMBJc"})
                    #Can separate the experience_context and experience_skills via indexing'''