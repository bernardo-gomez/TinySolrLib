#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
  'biblio' class parses a MARC record represented as 
   a list of plain-text strings. it contains a set
   of methods to convert MARC fields to text fields intended
   for solr use.
   
"""
__author__ = 'bernardo gomez'
__date__ = 'july 2020'

import os
import sys
import re

class Record:
   def __init__(self,marc_record):
      """
         it receives a marc record in marcEdit format
         creates a list of MARC text strings.
      """
      self.marc=[]
      self.marc=marc_record.split("\n")
      self.record=marc_record
      return

   def __str__(self):

     return self.record

   def get_leader(self):
      """
         it retrieves the MARC leader
         from the plain-text list.
      """
      leader=""
      for line in self.marc:
         if line[0:4] == "=LDR":
            leader=line[6:]
            break
      return leader

   def get_resource_type(self):
 
# http://www.oclc.org/bibformats/en/fixedfield/type.html
      """
         it parses the leader to retrieve the resource type.
      """
      leader=self.get_leader()
      r_type=""
      map={'aa':'Book','ac':'Book',
        'ad':'Book','am':'Book',
        'ta':'Book', 'tc':'Book','td':'Book', 'tm':'Book',
        'ab':'Periodical','ai':'Periodical',
        'as':'Periodical',
        'ca':'Score', 'cb':'Score','cc':'Score',
        'cd':'Score', 'ci':'Score','cm':'Score','cm':'Score',
        'ea':'Map','eb':'Map','ec':'Map','ed':'Map','ei':'Map',
        'em':'Map','es':'Map',
        'im':'Sound recording','it': 'Sound recording',
        'ja':'Sound recording','jb':'Sound recording','jc':'Sound recording',
        'jd':'Sound recording','ji':'Sound recording','jm':'Sound recording',
        'js':'Sound recording',
        'ga':'Video', 'gb':'Video', 'gc':'Video', 'gd':'Video',
        'gi':'Video', 'gm':'Video', 'gs':'Video',
        'pc':'Archive', 'pa':'Archive', 'pm':'Archive',
        'ma':'Computer file','mb':'Computer file','mc':'Computer file',
        'md':'Computer file','mi':'Computer file','mm':'Computer file',
        'ms':'Computer file'
      }
     
      leader0607=leader[6:8]
      try:
         r_type=map[leader0607]
      except:
         sys.stderr.write("rtype failed:"+str(leader0607)+"\n")
      return r_type

   def get_isbn(self):
      isbn=""
      digits=re.compile("(\d+)(.*)")
      for field in self.marc:
          if field[0:4] == "=020":
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == "a":
                       m=digits.match(subf[1:])
                       if m:
                          isbn=str(m.group(1))
                          return isbn
      return isbn

   def get_recordid(self):
      recid=""
      digits=re.compile("(\d+)(.*)")
      for field in self.marc:
          if field[0:4] == "=001":
               text=field[6:]
               m=digits.match(text)
               if m:
                  recid=str(m.group(1))
                  return recid
      return recid

   def get_oclc_string(self):
      """
        it retrieves the OCLC number based
        on the MARC 035.
      """
      oclc_number=""
      oclc_string=""
      oclc_1=re.compile("o(\d+)")
      oclc_2=re.compile("ocm(\d+)")
      oclc_3=re.compile("ocn(\d+)")
      oclc_4=re.compile("\(OCoLC\)(\d+)")
      found=False
      for field in self.marc:
          if field[0:4] == "=035":
               text=field[8:]
               subfield=text.split("$")
               for sf in subfield:
                  if sf != "":
                     if sf[0:1] == 'a':
                       m=oclc_1.match(sf[1:])
                       if m:
                         oclc_number=m.group(1)
                         found=True
                         break
                       m=oclc_2.match(sf[1:])
                       if m:
                          oclc_number=m.group(1)
                          found=True
                          break
                       m=oclc_3.match(sf[1:])
                       if m:
                         oclc_number=m.group(1)
                         found=True
                         break
                       m=oclc_4.match(sf[1:])
                       if m:
                          oclc_number=m.group(1)
                          found=True
                          break
               if found:
                    oclc_string="http://www.worldcat.org/oclc/"+str(oclc_number)
      return oclc_string

   def get_title(self):
      title=""
      title_880=""
      subfa=""
      subfb=""
      subfa_880=""
      subfb_880=""
      title_is_880=False
      for field in self.marc:
          if field[0:4] == "=245":
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == "a":
                       subfa=str(subf[1:])
                    elif subf[0:1] == "b":
                       subfb=str(subf[1:])
               title=subfa+" "+subfb
               title=title.replace("/","")
          if field[0:4] == "=880" and not title_is_880:
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == "6":
                        if subf[1:4] == "245":
                            title_is_880=True
                    elif subf[0:1] == "a":
                        subfa_880=str(subf[1:])
                    elif subf[0:1] == "b":
                        subfb_880=str(subf[1:])
               if title_is_880:
                   title_880=subfa_880+" "+subfb_880
                   title_880=title_880.replace("/","")
      if title_880 != "":
           title=title_880
      return title

   def get_language(self):
      """
        it retrieves the language based on the
        MARC 008.
      """
      language=""
      for field in self.marc:
          if field[0:4] == "=008":
               language=field[41:44]
               return str(language)
      return language

   def get_author(self):
      """
         it produces a list of names based on the
         MARC 100 and MARC 700. It disregards punctuation ( dot, comma)
      """
      name_list=[]
      name_880_list=[]
      name_is_880=False
      for field in self.marc:
          if field[0:4] == "=100":
               ignore_it=False
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == "6":
                        ignore_it=True
                    if subf[0:1] == "a":
                      name=subf[1:]
                      name=name.replace(",","")
                      name=name.replace(".","")
                      name=name.replace("/","")
               if not ignore_it:
                 name_list.append(name)
          elif field[0:4] == "=700":
               ignore_it=False
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == "6":
                        ignore_it=True
                    if subf[0:1] == "a":
                      name=subf[1:]
                      name=name.replace(",","")
                      name=name.replace(".","")
                      name=name.replace("/","")
               if not ignore_it:
                  name_list.append(name)
          elif field[0:4] == "=880":
               name_is_880=False
               text=field[8:]
               subfield=text.split("$")
               name_880=""
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == "6":
                        if subf[1:4] == "700":
                            name_is_880=True
                        if subf[1:4] == "100":
                            name_is_880=True
                    elif subf[0:1] == "a":
                           name_880=subf[1:]
                           name_880=name_880.replace('\u060c',"")
                           name_880=name_880.replace(".","")
                           name_880=name_880.replace("/","")
                           name_880=name_880.replace(",","")
               if name_is_880:
                  name_880_list.append(name_880)
        # '\u060c' arabic comma
#                      if subf[len(subf)-1] == '\u060c':
#  arabic semicolon ؛ U+061B
#  .  U+002E
      name_list=name_list+name_880_list
      return name_list

   def get_creator(self):
      """
         it retrieves the author's name based on the
         MARC 100 (subfield "a" only). It normalizes personal name: "namex, namey."
      """
      name=""
      name_880=""
      name_is_880=False
      for field in self.marc:
          if field[0:4] == "=100":
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == "a":
                      if subf[len(subf)-1] == ',':
                         name=subf[1:len(subf)-1]+"."
                      else:
                         name=subf[1:]
                      name=name.replace("..",".")
          if field[0:4] == "=880" and not name_is_880:
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == "6":
                        if subf[1:4] == "100":
                            name_is_880=True
                    elif subf[0:1] == "a":
                        subfa_880=str(subf[1:])
                        name_880=subfa_880
               if name_is_880:
                   name_880=name_880.replace("..",".")
      if name_is_880 :
           name=name_880
      return name

   def get_contributor(self):
      """
         it produces a list of personal names based on the
         MARC 700 (subfield "a" only) . It normalizes personal name: "namex, namey."
      """
      name_list=[]
      name_list_880=[]
      name_is_880=False
      name_880=""
      for field in self.marc:
          if field[0:4] == "=700":
               ignore_it=False
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == "6":
                        ignore_it=True
                    if subf[0:1] == "a":
                      if subf[len(subf)-1] == ',':
                         name=subf[1:len(subf)-1]+"."
                      else:
                         name=subf[1:]
               if not ignore_it:
                 name=name.replace("..",".")
                 name_list.append(name)
          if field[0:4] == "=880":
               name_is_880=False
               text=field[8:]
               subfield=text.split("$")
               name_880=""
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == "6":
                        if subf[1:4] == "700":
                            name_is_880=True
                    elif subf[0:1] == "a":
                           name_880=subf[1:]
        # '\u060c' arabic comma
#                      if subf[len(subf)-1] == '\u060c':
#  arabic semicolon ؛ U+061B
#  .  U+002E
               if name_880 != "" and name_is_880:
                   name_list_880.append(name_880)

      if len(name_list_880)  > 0:
           name_list=name_list_880+name_list
      return name_list

   def get_publication_info(self):
      """
        it rerieves publication information  based on the
        MARC 264
     """
#=264  \1$aMadrid :$bEdiciones Lengua de Trapo,$c2000.
      publication_info=""
      subfa=""
      subfb=""
      subfc=""
      for field in self.marc:
          if field[0:4] == "=264" and str(field[7:8]) == '1':
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == 'a':
                         subfa=subf[1:]
                         subfa=subfa.replace("[","")
                         subfa=subfa.replace("]","")
                    elif subf[0:1] == 'b':
                         subfb=subf[1:]
                    elif subf[0:1] == 'c':
                         subfc=subf[1:]
                         subfc=subfc.replace("[","")
                         subfc=subfc.replace("]","")
               publication_info=subfa+" "+subfb+" "+str(subfc)
          if publication_info == "":
            if field[0:4] == "=260":
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == 'a':
                         subfa=subf[1:]
                         subfa=subfa.replace("[","")
                         subfa=subfa.replace("]","")
                    elif subf[0:1] == 'b':
                         subfb=subf[1:]
                    elif subf[0:1] == 'c':
                         subfc=subf[1:]
                         subfc=subfc.replace("[","")
                         subfc=subfc.replace("]","")
               publication_info=subfa+" "+subfb+" "+str(subfc)
               return publication_info
          
      return publication_info
##

   def get_publisher(self):
      """
        it rerieves publication information  based on the
        MARC 264
     """
#=264  \1$aMadrid :$bEdiciones Lengua de Trapo,$c2000.
      publisher=""
      subfa=""
      subfb=""
      for field in self.marc:
          if field[0:4] == "=264" and str(field[7:8]) == '1':
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == 'a':
                         subfa=subf[1:]
                         subfa=subfa.replace("[","")
                         subfa=subfa.replace("]","")
                    elif subf[0:1] == 'b':
                         subfb=subf[1:]
                         subfb=subfb.replace(",","")
               publisher=subfa+" "+subfb

          if publisher == "":
            if field[0:4] == "=260":
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == 'a':
                         subfa=subf[1:]
                         subfa=subfa.replace("[","")
                         subfa=subfa.replace("]","")
                    elif subf[0:1] == 'b':
                         subfb=subf[1:]
                         subfb=subfb.replace(",","")
               publisher=subfa+" "+subfb
               return publisher
          
      return publisher

   def get_publication_date(self):
      """
        it rerieves publication information  based on the
        MARC 264
      """
      publication_date=""
      subfc=""
      for field in self.marc:
          if field[0:4] == "=264" and str(field[7:8]) == '1':
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == 'c':
                         subfc=subf[1:]
                         subfc=subfc.replace("[","")
                         subfc=subfc.replace("]","")
                         subfc=subfc.replace(".","")
               publication_date=subfc
               return publication_date

          if publication_date == "":
            if field[0:4] == "=260":
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == 'c':
                         subf=subf[1:]
                         subfc=subfc.replace("[","")
                         subfc=subfc.replace("]","")
                         subfc=subfc.replace(".","")
               publication_date=subfc
               return publication_date
      return publication_date
##
   def get_topic(self):
      """
        it retrieves information  based on the
        MARC 650. BUG: It returns a list of 650 (subfield a) entries.
      """
      topic=[]
      subfa=""
      for field in self.marc:
          if field[0:4] == "=650":
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                    if subf[0:1] == 'a':
                         subfa=subf[1:]
                         topic.append(subfa)
      unique_topic=set(topic)
      topic=list(unique_topic)
      return topic

   def get_genre(self):
      """
        it retrieves information  based on the
        MARC 655. BUG: It returns a list of 655 (subfield a) entries.
      """
      genre=[]
      subfa=""
      for field in self.marc:
          if field[0:4] == "=655":
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                    if subf[0:1] == 'a':
                         subfa=subf[1:]
                         genre.append(subfa)
      unique_genre=set(genre)
      genre=list(unique_genre)
      return genre



   def get_number_pages(self):
      """
         it retrieves page information based on the
         MARC 300
      """
      pages_string=""
#300|  |$$a274 pages ;$$c24 cm.
      pages=re.compile("[^0-9]*([0-9]+) pages.*")
      for rec in self.marc:
         if rec[0:3] == "300":
            text=rec[7:]
            subfield=text.split("$$")
            for sf in subfield:
               if sf != "":
                 if sf[0:1] == 'a':
                   m=pages.match(str(sf[1:]))
                   if m:
                     pages_string="\"numberOfPages\": "+"\""+m.group(1)+"\""
                     #print pages_string

      return pages_string


   def get_book_contributor_info(self):
      """
         it retrieves book contributor based on the
         MARC 700 and the contributor's role.
      """
      name=""
      name_string=""
      contributor_role="contributor"
      editor_list=[]
      contributor_list=[]
      translator_list=[]
      illustrator_list=[]
      contributor_list=[]
      producer_list=[]

      for rec in self.marc:
         if rec[0:3] == "700":
           deathdate=""
           birthdate=""
           text=rec[7:]
           #print text
           contributor_role="contributor"
           subfield=text.split("$$")
           contrib_name=""
           name=""
           for sf in subfield:
             if sf != "":
                if sf[0:1] == "a":
                   contrib_name=sf[1:]
                   contrib_name=contrib_name.rstrip(",")
                elif sf[0:1] == "d":
                      date=sf[1:]
                      date=date.rstrip(".")
                      date_info=date.split("-")
                      #sys.stderr.write("date:"+str(date_info)+"\n")
                      if date_info[0] != "":
                         birthdate=date_info[0]
                      if date_info[1] != "":
                         deathdate=date_info[1]
                elif sf[0:1] == "e":
                   this_role=sf[1:].lower()
                   this_role=this_role.replace(".","")
                   role_word=this_role.split(" ")
                   if "editor" in role_word:
                      contributor_role="editor"
                   elif "translator" in role_word:
                      contributor_role="translator"
                   elif "illustrator" in role_word:
                      contributor_role="illustrator"
                   elif "producer" in role_word:                  
                       contributor_role="producer"
                   else:
                       contributor_role="contributor"
           if contrib_name != "":
                 name+="{\"name\":\""+contrib_name+"\""
                 if birthdate != "":
                      name+=","+"\n"+"  \"birthDate\": \""+birthdate+"\""
                 if deathdate != "":
                      name+=","+"\n"+"  \"deathDate\": \""+deathdate+"\""+"\n"
                 name+="},\n"
                 if contributor_role == "editor":
                    editor_list.append(name)
                    name=""
                 if contributor_role == "translator":
                    translator_list.append(name)
                    name=""
                 if contributor_role == "producer":
                    producer_list.append(name)
                    name=""
                 if contributor_role == "contributor":
                    contributor_list.append(name)
                    name=""
                 if contributor_role == "illustrator":
                    illustrator_list.append(name)
                    name=""

         elif rec[0:3] == "x10":  ### exclude 710 for the time being
           deathdate=""
           birthdate=""
           text=rec[7:]
           #print text
           subfield=text.split("$$")
           contrib_name=""
           name=""
           for sf in subfield:
             if sf != "":
                if sf[0:1] == "a":
                   contrib_name=sf[1:]
                   contrib_name=contrib_name.rstrip(",")

                
           if contrib_name != "":
                 name+="{\"name\":\""+contrib_name+"\""
                 if birthdate != "":
                      name+=","+"\n"+"  \"birthDate\": \""+birthdate+"\""
                 if deathdate != "":
                      name+=","+"\n"+"  \"deathDate\": \""+deathdate+"\""+"\n"
                 name+="},\n"
                 if contributor_role == "editor":
                    editor_list.append(name)
                    name=""
                 if contributor_role == "translator":
                    translator_list.append(name)
                    name=""
                 if contributor_role == "producer":
                    producer_list.append(name)
                    name=""
                 if contributor_role == "contributor":
                    contributor_list.append(name)
                    name=""
                 if contributor_role == "illustrator":
                    illustrator_list.append(name)
                    name=""
      if len(contributor_list) > 0:
         name_string+="\"contributor\": ["+"\n"
         for entry in contributor_list:
           name_string+=entry
         name_string=name_string.rstrip("\n")
         name_string=name_string.rstrip(",")
         name_string+="\n],"
      if len(editor_list) > 0:
         name_string+="\"editor\": ["+"\n"
         for entry in editor_list:
           name_string+=entry
         name_string=name_string.rstrip("\n")
         name_string=name_string.rstrip(",")
         name_string+="\n],\n"
      if len(translator_list) > 0:
         name_string+="\"translator\": ["+"\n"
         for entry in translator_list:
           name_string+=entry
         name_string=name_string.rstrip("\n")
         name_string=name_string.rstrip(",")
         name_string+="\n],"
      if len(illustrator_list) > 0:
         name_string+="\"illustrator\": ["+"\n"
         for entry in illustrator_list:
           name_string+=entry
         name_string=name_string.rstrip("\n")
         name_string=name_string.rstrip(",")
         name_string+="\n],"
      if len(producer_list) > 0:
         name_string+="\"producer\": ["+"\n"
         for entry in producer_list:
           name_string+=entry
         name_string=name_string.rstrip("\n")
         name_string=name_string.rstrip(",")
         name_string+="\n],"
      name_string=name_string.rstrip("\n")
      name_string=name_string.rstrip(",")
      return name_string


   def display_record(self):
      """
        it sends string to the HTTP client.
      """
      for line in self.marc:
         sys.stderr.write(line+"\n")

      return 0

   def get_description(self):
      """
         it retrieves resource description  based on the
         MARC 520.
      """
      description_string=""
      for rec in self.marc:
         if rec[0:3] == "520":
           text=rec[7:]
           subfield=text.split("$$")
           for sf in subfield:
             if sf != "":
                if sf[0:1] == "a":
                   description=sf[1:]
                   description=description.replace("\"","")
                   description_string="\"description\": "+"\""+description+"\""
                   break
      return description_string



   def get_url(self):
      """
         it retrieves a URL based on the
         MARC  856.
      """
      url=""
      for field in self.marc:
          if field[0:4] == "=856":
               emory_resource=False
               if str(field[6:8]) == "40":
                  text=field[8:]
                  subfield=text.split("$")
                  for subf in subfield:
                    if subf != "":
                       if subf[0:1] == "u":
                            url=subf[1:]
                       if subf[0:1] == "z":
                           if subf[1:16] == "Online resource":
                               emory_resource=True
                  if emory_resource:
                     return url
      return url
