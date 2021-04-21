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
import json
import re
import biblio
import urllib.parse

class new_page:
   def __init__(self,html_file):
      """
         new_page receives an html_file and creates a corresponding 
         html_string.
      """
      self.html_string=""
      with open(html_file) as f:
            for line in f:
               self.html_string+=line
      return

   def __str__(self):
     """
        __str__ is a representation of html_string
     """
     return self.html_string

   def full_page(self,response,webserver_host,cgi_path,search_script):
     """
        full_page builds the html page that displays a single record.
        full_page receives 
          response: the solr description of the record,
          webserver_host: host name of the search platform,
          host_cgi: CGI path,
          search_script: CGI script
       full_page returns the html string and a return code.
                return code = 1 is failure,
                return code = 0 is success.
     """
     try:
          jsonResponse = response.json()
     except:
         print("connection to solr server failed ",file=sys.stderr)
         return "System error(31). Not a json response",1

     record_text=jsonResponse["response"]["docs"][0]["record"][0]
     try:
               online_access=jsonResponse["response"]["docs"][0]["link"][0]
     except:
                online_access=""
 # extract BIB elements from MARC record.
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
     title=str(title)
     page_string=self.html_string
     page_string=page_string.replace("<!--TITLE=-->",title)
           #print_error(creator)

     if creator != "":
           user_query="\""+creator+"\""
           quote_user_query=urllib.parse.quote(user_query)
           search_url=webserver_host+cgi_path+search_script+"?query="+quote_user_query+"&fq=creator:"+quote_user_query
           main_author="<tr><th>Main Author:</th><td><span><a style=\"font-size: large\" href=\""+search_url+"\">"+creator+"</a></span></td></tr>" 
           page_string=page_string.replace("<!--MAIN_AUTHOR=-->",main_author)
     if len(contributor) > 0:
           contrib_list="<tr><th>Contributors:</th><td>"
           for this_contrib in contributor:
                   quote_user_query="\""+this_contrib+"\""
                   quote_user_query=urllib.parse.quote(quote_user_query)
                   search_url=webserver_host+cgi_path+search_script+"?query="+quote_user_query+"&fq=contributor:"+quote_user_query
                   item="<div><a style=\"font-size:large\" href=\""+search_url+"\">"+this_contrib+"</a></div>"
                   contrib_list+=item 
           contrib_list=contrib_list+"</td></tr>"
           page_string=page_string.replace("<!--OTHER_AUTHORS=-->",contrib_list)
     if len(genre)+ len(topic) > 0:
                subject_list=""
                subject_list="<tr><th>Subject:</th><td>"
                for g_item in genre:
                   query="\""+g_item+"\""
                   quote_query=urllib.parse.quote(query)
                   search_url=webserver_host+cgi_path+search_script+"?query="+quote_query+"&fq=genre:"+quote_user_query
                   item="<div><a style=\"font-size:large\" href=\""+search_url+"\">"+g_item+"</a></div>"
                   subject_list+=item 
                for t_item in topic:
                   query="\""+t_item+"\""
                   quote_query=urllib.parse.quote(query)
                   search_url=webserver_host+cgi_path+search_script+"?query="+quote_query+"&fq=topic:"+quote_user_query
                   item="<div><a style=\"font-size:large\" href=\""+search_url+"\">"+t_item+"</a></div>"
                   subject_list+=item 
                subject_list=subject_list+"</td></tr>"
                page_string=page_string.replace("<!--SUBJECTS=-->",subject_list)
     if online_access != "":
                online="<tr><th>Online access:</th><td>"
                item="<div><a style=\"font-size:large\" href=\""+online_access+"\" target=\"_blank\">Available</a></div>"
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

   def dym_spell(self,response,user_query,webserver_host,cgi_path,search_script):
       """
        dym_spell builds the html page that displays a Did You Mean link.
        dym_spell receives 
          response: the solr description of the spelling suggestion,
          user_query: user query,
          webserver_host: host name of the search platform,
          host_cgi: CGI path,
          search_script: CGI script
       dym_spell returns the html string and a return code.
                return code = 1 is failure,
                return code = 0 is success.
       """
       page_string=self.html_string

       try:
          jsonResponse = response.json()
       except:
         print("connection to solr server failed ",file=sys.stderr)
         return "System error(21). Not a json response",1
  

       if jsonResponse["responseHeader"]["status"]  != 0:
             print ("solr error",file=sys.stderr)
             return "System error(6)",1

       in_line=re.compile(r'(.*<input type="text".*?value=")(.*?")(.*?>)(.*)',flags=re.DOTALL)

       if "spellcheck" not in jsonResponse:
              no_results='<div><h2>No Results Found</h2></div>'
              page_string=page_string.replace("<!--NORESULTS=-->",no_results)
              user_query=urllib.parse.unquote(user_query,encoding='utf-8')
              m=in_line.match(page_string)
              if m:
                 page_string=m.group(1)+user_query+'"'+m.group(3)+m.group(4)
              return page_string,0

       if len(jsonResponse["spellcheck"]["collations"]) == 0:
              no_results='<div><h2>No Results Found</h2></div>'
              page_string=page_string.replace("<!--NORESULTS=-->",no_results)
              user_query=urllib.parse.unquote(user_query,encoding='utf-8')
              m=in_line.match(page_string)
              if m:
                 page_string=m.group(1)+user_query+'"'+m.group(3)+m.group(4)
              return page_string,0
       suggested=jsonResponse["spellcheck"]["collations"][1]["collationQuery"]
       did_you_mean=str(suggested)
       search_uri=webserver_host+cgi_path+search_script+"?query="+did_you_mean
       did_you_mean='<div><span><h2>Did you mean <a href="'+search_uri+'">'+did_you_mean+'</a>?</h2></span></div>'
       user_query=urllib.parse.unquote(user_query,encoding='utf-8')
       m=in_line.match(page_string)
       if m:
                 page_string=m.group(1)+user_query+'"'+m.group(3)+m.group(4)
       page_string=page_string.replace("<!--DIDYOUMEAN=-->",did_you_mean)
       return page_string,0

   def record_list(self,response,user_query,webserver_host,cgi_path,search_script,refine_results,facet_script,page_size,record_count_marker,facet_marker,previous_marker,next_marker,full_record_script,results_marker):
      """
        record_list builds the html page that displays a list of records
            in brief format.
        record_list receives 
          response: the the solr description of records,
          user_query: user query,
          webserver_host: host name of the search platform,
          host_cgi: CGI path,
          search_script: CGI script that performs a solr search,
          refine_results: the html template for the facet display,
          facet_script: the script that searches a given facet,
          page_size: maximum number of records in a page,
          record_count_marker: place holder for number of records,
          facet_marker: place holder for facet display,
          previous_marker: place holder for link to previous page,
          next_marker: place holder for link to next page,
          full_record_script: CGI script that displays a single record,
          results_marker: place holder for record list,
        record_list returns the html string and a return code,
                return code = 1 is failure,
                return code = 0 is success.
      """
      try:
          jsonResponse = response.json()
      except:
         print("connection to solr server failed ",file=sys.stderr)
         return "System error(21). Not a json response",1

      refine_result_string=""
      number_found=jsonResponse["response"]["numFound"]
      start_record=jsonResponse["response"]["start"]

## read html template for facet list.
      with open(refine_results) as f:
            for line in f:
                refine_result_string+=line

      facet_info=jsonResponse["facet_counts"]
      facet_fields=facet_info["facet_fields"]
      facet_list={}
      for facet, value in facet_fields.items():
            state="get_item"
            item_list=[]
            string=""
            for item in value:
               if state == "get_item":
                  string=str(item)
                  state="get_count"
               else:
                  string=string+"_|_"+str(item)
                  item_list.append(string)
                  string=""
                  state="get_item"
            facet_list.update({facet:item_list})

      req_list=""
      for key,value in facet_list.items():
            html_marker="<!--"+str(key)+"=-->"
            for v in value:
               instance=v.split("_|_")
               if len(instance) == 2:
                  instance_value=instance[0]
                  instance_count=instance[1]
                  quote_user_query=urllib.parse.quote(user_query)
                  quote_instance_value=urllib.parse.quote(instance_value)
                  facet_query='&q='+quote_user_query+'&fq='+key+':'+str(quote_instance_value)
                  facet_request=webserver_host+cgi_path+facet_script+'?'+facet_query
                  req='<li><span><a href="'+facet_request+'">'+instance_value+'</a>'+'</span>'+'<span>'+"  "+str(instance_count)+'</span>'+'</li>'
                  req_list+=req
            refine_result_string=re.sub(html_marker,req_list,refine_result_string)
            req_list=""
      ###
##  solr found multiple matches. Display count number.
      result_count="Number of records: "+str(number_found)
      result_count="<h3>"+result_count+"</h3>"

##  solr found multiple matches. Display list of records.
      ## build results list as an HTML string
      result_page=self.html_string

      result_page=re.sub(record_count_marker,result_count,result_page)
      result_page=re.sub(facet_marker,refine_result_string,result_page)
#####
####
      record_table=""
      record_table='<div class="RecResults">'
      record_table+='<table class="RecordTable">'
      record_table+='<tbody>'
      for rec in jsonResponse["response"]["docs"]:
            record_id=rec["id"]
            record_text=rec["record"][0]
            marc=biblio.Record(record_text)
            #outcome,rec_title=get_title(record_text)
            rec_title=marc.get_title()
            #outcome,author_str=get_author(record_text)
            author_str=marc.get_creator()
            if author_str != "":
               author_str="by "+author_str
            publication_info=marc.get_publication_info()
            title_url=webserver_host+cgi_path+full_record_script+"?id="+str(record_id)
            record_title=rec_title
            record_table+='<tr>'
            record_table+='<td>'
            record_table+='<div class="SummaryFields">'
            record_table+='<h2>'
            record_table+='<a href="'+title_url+'">'+str(record_title)+'</a>'
            record_table+='</h2>'
            if author_str !=  "":
               record_table+='<h3>'+author_str+'</h3>'
            record_table+='<h3>'+publication_info+'</h3>'
            record_table+='</div>'
            record_table+='</td>'
            record_table+='</tr>'
      record_table+='</tbody>'
      record_table+='</table>'
      record_table+='</div>'
      result_page=re.sub(results_marker,record_table,result_page)

##  compute next_page and previous_page links
##  based on number_found, rows, start_record
##  if (start_record + rows) >=  number_found: no next_page
##  if (start_record -rows >= 0): create link to previous_page [start_record= start_record - rows]
##  if (start_record - rows) < 0 : no previous_page
##  if (start_record + rows) < number_found: create link to next_page [start_record= start_record+rows ]
##
##    result_page=re.sub(previous_marker,previouspage_element,result_page)
##    result_page=re.sub(next_marker,nextpage_element,result_page)
##
      nextpage_link=''
      previouspage_link=''
      previouspage_element=''
      nextpage_element=''
      if int(start_record) + int(page_size) < int(number_found):
        next_page=str(int(start_record)+int(page_size))
        quote_user_query=urllib.parse.quote(user_query)
        nextpage_link=webserver_host+cgi_path+'search?query='+quote_user_query+'&next='+next_page
        nextpage_element='<span>  <a href="'+nextpage_link+'" title="Next page"><b>NEXT</b></a>   </span>'
      if int(start_record) - int(page_size) >= 0:
        next_page=str(int(start_record)-int(page_size))
        previouspage_link=webserver_host+cgi_path+'search?query='+quote_user_query+'&next='+next_page
        previouspage_element='<span> <a href="'+previouspage_link+'" title="Previous page"><b>PREVIOUS</b></a>  </span>'

      result_page=re.sub(previous_marker,previouspage_element,result_page)
      result_page=re.sub(next_marker,nextpage_element,result_page)
      in_line=re.compile(r'(.*<input type="text".*?value=")(.*?")(.*?>)(.*)',flags=re.DOTALL)
      user_query=urllib.parse.unquote(user_query,encoding='utf-8')
      m=in_line.match(result_page)
      if m:
           result_page=m.group(1)+user_query+'"'+m.group(3)+m.group(4)

      return result_page,0

if __name__=="__main__":
    page=new_page("/home/bernardo/Webserver/Documents/euclid/full_record.html")
    print(page)
    
