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
      subfa=""
      subfb=""
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
      for field in self.marc:
          if field[0:4] == "=100":
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == "a":
                      name=subf[1:]
                      name=name.replace(",","")
                      name=name.replace(".","")
                      name_list.append(name)
          elif field[0:4] == "=700":
               text=field[8:]
               subfield=text.split("$")
               for subf in subfield:
                  if subf != "":
                    if subf[0:1] == "a":
                      name=subf[1:]
                      name=name.replace(",","")
                      name=name.replace(".","")
                      name_list.append(name)
      return name_list

   def get_creator(self):
      """
         it retrieves the author's name based on the
         MARC 100 (subfield "a" only). It normalizes personal name: "namex, namey."
      """
      name=""
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
                      return name
      return name

   def get_contributor(self):
      """
         it produces a list of personal names based on the
         MARC 700 (subfield "a" only) . It normalizes personal name: "namex, namey."
      """
      name_list=[]
      for field in self.marc:
          if field[0:4] == "=700":
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
                      name_list.append(name)
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
      for rec in self.lines:
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

      for rec in self.lines:
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
      for line in self.lines:
         sys.stderr.write(line+"\n")

      return 0

   def get_description(self):
      """
         it retrieves resource description  based on the
         MARC 520.
      """
      description_string=""
      for rec in self.lines:
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
               if str(field[6:8]) == "40":
                  text=field[8:]
                  subfield=text.split("$")
                  for subf in subfield:
                    if subf != "":
                       if subf[0:1] == "u":
                            url=subf[1:]
                            return url
      return url


if __name__=="__main__":
  record="""=LDR  ^^^^^cjm^a2200577Ia^4500\n=001  990007175530302486\n=005  20160418211004.0\n=007  sd^fungnn|||eu\n=008  021212p20021973xxujzn^^^i^^^^^^^^^^eng^d\n=024  1\\$a696998682429\n=028  02$a9699-86824-2$bColumbia/Legacy\n=028  00$a9362-45221-2$bWarner Bros.\n=028  00$a9 45221-2$bWarner Bros.\n=033  00$a19730708$b6044$cM6\n=033  20$a19840708$a19910708$b6044$cM6\n=033  00$a19910717$b5834$cN5\n=035  \\\\$a(Aleph)000717553EMU01\n=035  9\\$au2955438\n=035  \\\\$aocm51214070\n=035  \\\\$a(Sirsi) o51214070\n=035  \\\\$a(OCoLC)51214070\n=040  \\\\$aIXA$cIXA$dMDY$dOCLCQ$dUtOrBLW\n=082  04$a781.65\n=100  1\\$aDavis, Miles,$bperformer\n=245  14$aThe complete Miles Davis at Montreux$h[sound recording] /$cMiles.\n=246  30$aMiles Davis at Montreux\n=264  \\4$c℗2002\n=264  \\1$a[U.S.?] :$bColumbia/Legacy :$bMontreux Sounds,$c[2002]\n=300  \\\\$a20 sound discs :$bdigital ;$c4 3/4 in.\n=336  \\\\$aperformed music$bprm$2rdacontent\n=337  \\\\$aaudio$bs$2rdamedia\n=338  \\\\$aaudio disc$bsd$2rdacarrier\n=500  \\\\$a\"Contain[s] every single note that ... Miles Davis played at the Montreux Jazz Festival on Lake Geneva in Switzerland\"--P. 6 of book.\n=511  0\\$aMiles Davis, trumpet ; with, variously: Dave Liebman, reeds ; Kenny Garrett, Rick Margitza, David Sanborn, saxophone ; Bob Berg, saxophone, keyboards ; Reggie Lucas, Pete Cosey, John Scofield, Robben Ford, guitar ; Robert Irving III, Adam Holzman, Kei Akagi, Deron Johnson, George Duke, keyboards ; Michael Henderson, Darryl Jones, Felton Crews, Benny Rietveld, bass ; Richard Patterson, Foley, bass, vocal ; Al Foster, Vincent Wilburn Jr., Ricky Wellman, drums ; J. Mtume, percussion, synthesizer ; Steve Thornton, Marilyn Mazur, Munyungo Jackson, Erin Davis, percussion ; Wallace Roney, trumpet, flugelhorn ; Chaka Khan, vocal ; The Gil Evans Orchestra ; The George Gruntz Concert Jazz Band ; Quincy Jones, conductor.\n=518  \\\\$aRecorded live at the Montreux Jazz Festival, Montreux, Switzerland, July 8, 1973 and July 8, 1984-July 8, 1991; disc 20 recorded live in Nice, France, July 17, 1991.\n=500  \\\\$aMost selections previously unreleased; disc 19 previously released as Live at Montreux in 1993 (Warner Bros. 9362-45221-2 [i.e. 9 45221-2]).\n=500  \\\\$aCompact discs.\n=500  \\\\$aProgram notes by Nick Liebmann, Claude Nobs, and Adam Holzman (49 p. : ill., some col. ; 27 x 16 cm.) inserted in container.\n=505  0\\$aVariously (some titles repeated): Miles in Montreux '73 -- Ife -- Calypso frelimo -- Speak/That's what happened -- Star people -- What it is -- It gets better -- Something's on your mind -- Time after time -- Hopscotch/Star on Cicely -- Bass solo -- Jean-Pierre -- Lake Geneva -- Code M.D. -- Theme from Jack Johnson/One phone call/Street scenes/That's what happened -- Maze -- Human nature -- MD 1/Something's on your mind/MD 2 -- Ms. Morrisine -- Pacific Express -- Katia -- You're under arrest -- Jean-Pierre/You're under arrest/Then there were none -- Decoy -- New blues -- Wrinkle -- Tutu -- Splatch -- Al Jarreau -- Carnival time -- Burn -- Portia -- In a silent way -- Intruder -- Perfect way -- The senate/Me & U -- Movie star -- Heavy metal prelude -- Heavy metal -- Don't stop me now -- Tomaas -- Hannibal -- Mr. Pastorius -- Jilli -- Jo Jo -- Amandla -- Introduction by Claude Nobs & Quincy Jones -- Boplicity -- Introduction to \"Miles ahead\" medley -- Springsville -- Maids of Cadiz -- The Duke -- My ship -- Miles ahead -- Blues for Pablo -- Introduction to \"Porgy and Bess\" medley -- Orgone -- Gone, gone, gone -- Summertime -- Here come de honey man -- Introduction to \"Sketches of Spain\" -- The pan piper -- Solea.\n=650  \\0$aJazz.\n=650  \\0$aJazz vocals.\n=650  \\0$aJazz musicians.\n=650  \\0$aJazz musicians$zUnited States.\n=650  \\0$aLive sound recordings.\n=700  2\\$aCorea, Chick.$bpianist\n=700  2\\$aPuente,Tito.,$bmusician\n=710  2\\$aMontreux Sounds.\n=740  02$aLive at Montreux.\n=910  \\\\$aRDA ENRICHED\n=910  \\\\$aMARS\n=945  \\\\$aemu pmb\n=945  \\\\$a9DT$220080225\n=994  \\\\$aZ0$bEMU"a"""
  marc=Record(record)
  print(marc)
  print(marc.get_title())
  print(marc.get_creator())
  print(marc.get_contributor())
  print(marc.get_genre())
  print(marc.get_topic())
  print(marc.get_publication_info())
  print(marc.get_publication_date())
  print("publisher:",marc.get_publisher())
  print(marc.get_language())
  print(marc.get_resource_type())
  print(marc.get_oclc_string())
