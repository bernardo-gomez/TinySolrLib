#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
  'displaypage' class receives a solr jsonRespone and 
  produces an html page, based on a template provided
  by an input file. 
   
"""
__author__ = 'bernardo gomez'
__date__ = 'august 2020'

import os
import sys
import re
import biblio
import urllib.parse

class fullRecord:
   def __init__(self,html_file):
      """
      """
      self.html_string=""
      with open(html_file) as f:
            for line in f:
               self.html_string+=line
      return

   def __str__(self):

     return self.html_string

   def full_page(self,jsonResponse,user_query,webserver_host,cgi_path,search_script):
     """
     """

     record_text=jsonResponse["response"]["docs"][0]["record"][0]
     try:
               online_access=jsonResponse["response"]["docs"][0]["link"][0]
     except:
                online_access=""
     marc=biblio.Record(record_text)
     title=marc.get_title()
     creator=marc.get_creator()
     contributor=marc.get_contributor()
     resource_type=marc.get_resource_type()
     publication_info=marc.get_publication_info()
     genre=marc.get_genre()
     topic=marc.get_topic()
     language=marc.get_language()
     oclc_link=marc.get_oclc_string()
# <tr><th>Main Author:</th><td><span><a href="  /Find/Author/Home?author=Davis%2C+Miles.">Davis, Miles.</a></span></td></tr>
     title=str(title)
     page_string=self.html_string
     page_string=page_string.replace("<!--TITLE=-->",title)
           #print_error(creator)
#http://localhost:8983/solr/euclid/select?q=creator:"Davis, Miles."
# http://localhost/cgi-bin/search?query="Davis,%20Miles."&search_field=creator
# webserver_host='http://localhost' cgi_path='/cgi-bin/' search_script='search'

     if creator != "":
           user_query="\""+creator+"\""
           quote_user_query=urllib.parse.quote(user_query)
           search_url=webserver_host+cgi_path+search_script+"?query="+quote_user_query+"&search_field=creator"
           main_author="<tr><th>Main Author:</th><td><span><a href=\""+search_url+"\">"+creator+"</a></span></td></tr>" 
           page_string=page_string.replace("<!--MAIN_AUTHOR=-->",main_author)
     if len(contributor) > 0:
           contrib_list="<tr><th>Contributors:</th><td>"
           for this_contrib in contributor:
                   quote_user_query="\""+this_contrib+"\""
                   quote_user_query=urllib.parse.quote(quote_user_query)
                   search_url=webserver_host+cgi_path+search_script+"?query="+quote_user_query+"&search_field=contributor"
                   item="<div><a href=\""+search_url+"\">"+this_contrib+"</a></div>"
                   contrib_list+=item 
           contrib_list=contrib_list+"</td></tr>"
           page_string=page_string.replace("<!--OTHER_AUTHORS=-->",contrib_list)
     if len(genre)+ len(topic) > 0:
                subject_list=""
                subject_list="<tr><th>Subject:</th><td>"
                for g_item in genre:
                   query="\""+g_item+"\""
                   quote_query=urllib.parse.quote(query)
                   search_url=webserver_host+cgi_path+search_script+"?query="+quote_query+"&search_field=genre"
                   item="<div><a href=\""+search_url+"\">"+g_item+"</a></div>"
                   subject_list+=item 
                for t_item in topic:
                   query="\""+t_item+"\""
                   quote_query=urllib.parse.quote(query)
                   search_url=webserver_host+cgi_path+search_script+"?query="+quote_query+"&search_field=topic"
                   item="<div><a href=\""+search_url+"\">"+t_item+"</a></div>"
                   subject_list+=item 
                subject_list=subject_list+"</td></tr>"
                page_string=page_string.replace("<!--SUBJECTS=-->",subject_list)
     if online_access != "":
                online="<tr><th>Online access:</th><td>"
                item="<div><a href=\""+online_access+"\">Available</a></div>"
                online=online+item
                page_string=page_string.replace("<!--ONLINE_ACCESS=-->",online)
     if oclc_link != "":
                worldcat="<div><h2>"+"<a href=\""+oclc_link+"\" target=\"_blank\">"+"This item in Worldcat</a></h2></div>"
                page_string=page_string.replace("<!--WORLDCAT=-->",worldcat)
                staff_view=record_text
                page_string=page_string.replace("<!--STAFF_VIEW=-->",staff_view)
     try:
           authority_id=jsonResponse["response"]["docs"][0]["loc_authority_name"][0]
     except:
           authority_id=""
# http://worldcat.org/identities/lccn-n91005712/ <!--OCLC_IDENTITY_NETWORK=-->
     if authority_id != "":
               oclc_id_network="http://worldcat.org/identities/lccn-"+str(authority_id)+"/"
               id_network="<div><h2>"+"<a href=\""+oclc_id_network+"\" target=\"_blank\">"+"More about this author</a></h2></div>"
               page_string=page_string.replace("<!--OCLC_IDENTITY_NETWORK=-->",id_network)

     return page_string


if __name__=="__main__":
    page=fullRecord("/Users/bernardo/Webserver/Documents/euclid/full_record.html")
    print(page)
    
