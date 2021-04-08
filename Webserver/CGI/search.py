#!/usr/bin/env python3
"""
   It receives a query whose target is a solr server.
   The user query as sent by the web form is normalized:
      - if the query doesn't have a specific search field,
        then each term is made "required" by adding the "+" prefix.
      - if the query indicates a search field, then the
          query is not modified. this condition supports 
          facet queries, which are treated as strings, instead
          of a sequence of terms.
   
"""
__author__= 'bernardo gomez'
__date__ = 'september 2020'

import requests
from requests.exceptions import HTTPError

import json
import sys
import cgi
from pathlib import Path
import re
import biblio
import displaypage
import urllib.parse
import cgitb
cgitb.enable()


def main():
  """
   It expects a configuration file. 
   All error messages go to the standard error.
   The requests to the solr server are via solr's API.
   - If the result contains one record, then it 
   displays the full record.
   - If there are no results, then it invokes solr's
   spell feature and it produces a "did you mean?" link.
   - If the result contains multiple records, it displays a 
     list of records, along with the corresponding facet list.
  """
  if len(sys.argv) < 2:
       print_error("System error (1)")
       print("No configuration file",file=sys.stderr)
       return

  cfg_file=sys.argv[1]

  solr_host=''
  solr_path=''
  webserver_host=''
  cgi_path=''
  search_script=''
  facet_script=''
  full_record_script=''
  display_full_record=''
  display_results=''
  form_file=''
  refine_results=''
  facet_marker=''
  record_count_marker=''
  results_marker=''
  previous_marker=''
  next_marker=''
  page_size=""
  credentials=""
 
  failed=0
  if not Path(cfg_file).exists():
       print_error("System error (2)")
       failed+=1
       print("configuration file doesn't exist",file=sys.stderr)
       return 
 # retrieve configuration variables.

  cfg_pattern=re.compile("(.*?)=(.*)")
  with open(cfg_file) as f:
       for line in f:
          line=line.rstrip("\n")
          m=cfg_pattern.match(line)
          if m:
              if m.group(1) == "solr_host":
                 solr_host=m.group(2)
              if m.group(1) == "solr_path":
                 solr_path=m.group(2)
              if m.group(1) == "webserver_host":
                 webserver_host=m.group(2)
              if m.group(1) == "cgi_path":
                 cgi_path=m.group(2)
              if m.group(1) == "search_script":
                 search_script=m.group(2)
              if m.group(1) == "facet_script":
                 facet_script=m.group(2)
              if m.group(1) == "full_record_script":
                 full_record_script=m.group(2)
              if m.group(1) == "display_full_record":
                 display_full_record=m.group(2)
              if m.group(1) == "display_results":
                 display_results=m.group(2)
              if m.group(1) == "form_file":
                 form_file=m.group(2)
              if m.group(1) == "refine_results":
                 refine_results=m.group(2)
              if m.group(1) == "facet_marker":
                 facet_marker=m.group(2)
              if m.group(1) == "record_count_marker":
                 record_count_marker=m.group(2)
              if m.group(1) == "results_marker":
                 results_marker=m.group(2)
              if m.group(1) == "previous_marker":
                 previous_marker=m.group(2)
              if m.group(1) == "next_marker":
                 next_marker=m.group(2)
              if m.group(1) == "page_size":
                 page_size=m.group(2)
              if m.group(1) == "credentials":
                 credentials=m.group(2)

  if not Path(display_full_record).exists():
       failed+=1
       print(display_full_record, " not found",file=sys.stderr)

  if not Path(display_results).exists():
       print(display_results, " not found",file=sys.stderr)
       failed+=1

  if not Path(refine_results).exists():
       print(refine_results, " not found",file=sys.stderr)
       failed+=1

  if not Path(form_file).exists():
       print(form_file, " not found",file=sys.stderr)
       failed+=1

  if search_script == '':
       failed+=1
       print("search_script undefined ",file=sys.stderr)

  if facet_script == '':
       print("facet_script undefined ",file=sys.stderr)
       failed+=1

  if facet_marker == '':
       print("facet_marker undefined ",file=sys.stderr)
       failed+=1

  if record_count_marker == '':
       print("record_count_marker undefined ",file=sys.stderr)
       failed+=1

  if results_marker == '':
       print("results_marker undefined ",file=sys.stderr)
       failed+=1

  if previous_marker == '':
       print("previous_marker undefined ",file=sys.stderr)
       failed+=1

  if next_marker == '':
       print("next_marker undefined ",file=sys.stderr)
       failed+=1

  if page_size == '':
       print("page_size undefined ",file=sys.stderr)
       failed+=1

  if credentials == '':
       print("credentials undefined ",file=sys.stderr)
       failed+=1

  if failed > 0:
       print_error("System error (3)")
       return

#  read web form

  form = cgi.FieldStorage()
  if "query" not in form:
     print_form(form_file)
     return

  if "next" not in form:
     next_page=0
  else:
     next_page=form["next"].value

  search_field=""
  if "search_field" in form:
      search_field=form["search_field"].value

  user_query=form["query"].value

# basic safety step
  user_query=re.sub(r'<|>|;|\'|&','',user_query)

# normalize query for solr, if needed.
  normalized_q=user_query
  terms=user_query.split(" ")
  if search_field == "":
        normalized_q=""
## make all the terms "required" in the query by using "+" prefix
        for term in terms:
           if term !="":
              term=str(term)
              if term[0] != "+" and term[0] != "-":
                 if str(term) != "OR" and str(term) != "AND" and str(term) != "NOT":
                   normalized_q+="+"+str(term)+" "
              else:
                 normalized_q+=str(term)+" "

  #print("normalized:",normalized_q,file=sys.stderr)
  
  authorized_user,authorized_passwd=credentials.split("_|_")

  process_form(user_query,solr_host,solr_path,form_file,display_results,display_full_record,webserver_host,cgi_path,facet_script,facet_marker,full_record_script,results_marker,next_page,page_size,previous_marker,next_marker,search_field,search_script,refine_results,normalized_q,authorized_user,authorized_passwd,record_count_marker)
  return

def print_error(message):
     """
        It produces an HTML page with
        an error message when a system
        failure is detected.
     """
     print("Content-Type: text/html")    # HTML is following
     print()                             # blank line, end of headers
     print('<!DOCTYPE html>')
     print('<html lang="en-US">')
     print('<head>')
     print('<title>Error</title>')
     print('<meta charset="utf-8">')
     print('<meta name="viewport" content="width=device-width, initial-scale=1">')
     print('</head>')
     print('<body>')
     print("<H1>",message,"</H1>")
     print('</body>')
     print('</html>')
     return
   
def print_page(result_page):
    """
        It produces an HTML page with results
        based on the input string.
    """
    print("Content-Type: text/html")    # HTML is following
    print()                             # blank line, end of headers
    print(result_page)
    return

def print_form(form_file):
    """
        It produces an HTML page with webform
        based on the input file.
    """
    print("Content-Type: text/html")    # HTML is following
    print()                             # blank line, end of headers
    with open(form_file) as f:
       for line in f:
          print(line)
    return



def process_form(user_query,solr_host,solr_path,form_file,display_results,display_full_record,webserver_host,cgi_path,facet_script,facet_marker,full_record_script,results_marker,next_page,page_size,previous_marker,next_marker,search_field,search_script,refine_results,normalized_q,authorized_user,authorized_passwd,record_count_marker):
  
  """
    process_form receives the following parameters:
      user_query: as typed by the user;
      solr_host: solr hostname;
      solr_path: a CGI alias, for instance;
      form_file: it serves as an HTML template;
      display_results: file that serves as an HTML template;
      display_full_record: file that serves as an HTML template;
      webserver_host: hostname of the webserver that hosts these scripts;
      cgi_path: cgi directory for these scripts;
      facet_script: name of cgi script that queries facets;
      facet_marker: place holder in HTML display_results;
      record_count_marker: place holder in HTML display_results;
      full_record_script: name of cgi script that displays full record;
      results_marker: place holder in HTML display_results;
      next_page: number of record that starts current page;
      page_size: number of records to display in result page;
      previous_marker: place holder for link to previous page;
      next_marker: place holder for link to next page;
      search_field: name of qualifying field in user query;
      search_script: name of cgi script that performs query;
      refine_results: place holder to facet list in HTML page;
      normalized_q: sequence of search terms for solr search;
      authorized_user: authorized solr user;
      authorized_passwd: user's password;
   
   This function sends a request to the solr server via API and builds
   a result page after analisying the solr response.
   
   Facet fields are hard-coded:
     pubDate, language, resourceType, topic, genre, creator, contributor
     
  """
  from requests.auth import HTTPBasicAuth
  next_page=str(next_page)
  page_size=str(page_size)
  try:
      quote_user_query=urllib.parse.quote(normalized_q)
      if search_field != "":
         query=search_field+":"+quote_user_query
      else:
         query=quote_user_query  # don't normalize if search is qualified.

### API call to solr server
      search=solr_host+solr_path+'select?q='+query+'&facet=on&facet.field=pubDate&&facet.field=language&facet.field=resourceType&facet.field=topic&facet.field=genre&facet.field=creator&facet.field=contributor&facet.mincount=1&rows='+page_size+'&start='+next_page
      try:
         response = requests.get(search,auth=HTTPBasicAuth(authorized_user,authorized_passwd),timeout=10)
      except:
         print("connection to solr server failed ",file=sys.stderr)
         print_error("System error(4)")
         return
      if response.status_code != 200:
         if response.status_code == 401:
             print("connection to solr server failed. Bad credentials.",file=sys.stderr)
             print_error("System error(22). Bad credentials.")
             return
         else:
             print("connection to solr server failed. status code:",str(response.status_code),file=sys.stderr)
             print_error("System error(23).")
             return
      try:
         jsonResponse = response.json()
      except:
         print("connection to solr server failed ",file=sys.stderr)
         print_error("System error(21). Not a json response")
         return

#     print(jsonResponse["responseHeader"]["status"],file=sys.stderr)

      if jsonResponse["responseHeader"]["status"]  != 0:
         error_msg=jsonResponse["error"]["msg"]
         print ("solr error ",error_msg, file=sys.stderr)
         print_error("System error(5)")
         return

      number_found=jsonResponse["response"]["numFound"]
      start_record=jsonResponse["response"]["start"]
       #print(len(jsonResponse["response"]["docs"]))
      record_count=len(jsonResponse["response"]["docs"])
      #print ("Number of records",str(record_count),file=sys.stderr)
      if record_count == 1 and number_found == 1:
### Only one record found: display full record.
            full_record=displaypage.fullRecord(display_full_record)
            page_string=full_record.full_page(jsonResponse,user_query,webserver_host,cgi_path,search_script)
            print_page(page_string)
            return

      if record_count == 0:
###  No records found. Present correct spellings, if available.

          spell_req=solr_host+solr_path+'spell?spellcheck.q='+user_query+'&spellcheck=on'
          response = requests.get(spell_req,auth=HTTPBasicAuth(authorized_user,authorized_passwd),timeout=10)
          if response.status_code != 200:
             print ("solr error. return code:",str(response.status_code),file=sys.stderr)
             print_error("System error(24)")
             return

              
          jsonResponse = response.json()
          if jsonResponse["responseHeader"]["status"]  != 0:
             print ("solr error",file=sys.stderr)
             print_error("System error(6)")
             return

          page_string=""
          with open(form_file) as f:
              for line in f:
                  page_string+=line
          in_line=re.compile(r'(.*<input type="text".*?value=")(.*?")(.*?>)(.*)',flags=re.DOTALL)

          if "spellcheck" not in jsonResponse:
              no_results='<div><h2>No Results Found</h2></div>'
              page_string=page_string.replace("<!--NORESULTS=-->",no_results)
              user_query=urllib.parse.unquote(user_query,encoding='utf-8')
              m=in_line.match(page_string)
              if m:
                 page_string=m.group(1)+user_query+'"'+m.group(3)+m.group(4)
              print_page(page_string)
              return

          if len(jsonResponse["spellcheck"]["collations"]) == 0:
              no_results='<div><h2>No Results Found</h2></div>'
              page_string=page_string.replace("<!--NORESULTS=-->",no_results)
              user_query=urllib.parse.unquote(user_query,encoding='utf-8')
              m=in_line.match(page_string)
              if m:
                 page_string=m.group(1)+user_query+'"'+m.group(3)+m.group(4)
              print_page(page_string)
              return
          suggested=jsonResponse["spellcheck"]["collations"][1]["collationQuery"]
          did_you_mean=str(suggested)
          search_uri=webserver_host+cgi_path+search_script+"?query="+did_you_mean
          did_you_mean='<div><span><h2>Did you mean <a href="'+search_uri+'">'+did_you_mean+'</a>?</h2></span></div>'
          user_query=urllib.parse.unquote(user_query,encoding='utf-8')
          m=in_line.match(page_string)
          if m:
                 page_string=m.group(1)+user_query+'"'+m.group(3)+m.group(4)
          page_string=page_string.replace("<!--DIDYOUMEAN=-->",did_you_mean)
          print_page(page_string)
          return
###
## 
###
      refine_result_string=""

      with open(refine_results) as f:
            for line in f:
                refine_result_string+=line
##  solr found multiple matches. Display count number.
### show facets along with record list.
## facet example as returned by solr:
# "facet_counts":{
#   "facet_queries":{},
#   "facet_fields":{
#     "pubDate":[
#       "1989",2,
#       "2004",2,
#       "1994",1,
#     "language":[
#       "english",5,
#       "chinese",1]},
#   "facet_ranges":{},
#   "facet_intervals":{},
#   "facet_heatmaps":{}}

#     print(jsonResponse["facet_counts"],file=sys.stderr)
      facet_info=jsonResponse["facet_counts"]
      facet_fields=facet_info["facet_fields"]
#     print(facet_fields,file=sys.stderr)
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
#           print(facet,":",item_list,file=sys.stderr)
            facet_list.update({facet:item_list})
                    
      req_list=""
      for key,value in facet_list.items():
            html_marker="<!--"+str(key)+"=-->"
          # print(html_marker,file=sys.stderr)
            for v in value:
               instance=v.split("_|_")
               #print(instance,file=sys.stderr)
               if len(instance) == 2:
                  instance_value=instance[0]
                  instance_count=instance[1]
                  quote_user_query=urllib.parse.quote(user_query)
                  quote_instance_value=urllib.parse.quote(instance_value)
                  #facet_query='facet=on&q='+quote_user_query+'&facet.field='+key+'&facet_mincount=1&fq='+key+':'+str(quote_instance_value)
                  facet_query='&q='+quote_user_query+'&facet.field='+key+'&fq='+key+':'+str(quote_instance_value)
                  facet_request=webserver_host+cgi_path+facet_script+'?'+facet_query
                  req='<li><span><a href="'+facet_request+'">'+instance_value+'</a>'+'</span>'+'<span>'+"  "+str(instance_count)+'</span>'+'</li>'
                  req_list+=req
                  #print(req,file=sys.stderr)
            #print(req_list,file=sys.stderr)
            refine_result_string=re.sub(html_marker,req_list,refine_result_string)
            req_list=""
      #     print (key,"==>",value,file=sys.stderr)
      ### 
##  solr found multiple matches. Display count number.
      result_count="Number of records: "+str(number_found)
      result_count="<h3>"+result_count+"</h3>"

##  solr found multiple matches. Display list of records.
      ## build results list as an HTML string
      result_page=""
      with open(display_results) as f:
            for line in f:
                result_page+=line

      result_page=re.sub(record_count_marker,result_count,result_page)
      result_page=re.sub(facet_marker,refine_result_string,result_page)
#####
####
      record_table=""
      record_table='<div class="RecResults">'
      record_table+='<table class="RecordTable">'
      record_table+='<tbody>'
      for rec in jsonResponse["response"]["docs"]:
#           print("record_id:", rec["id"],file=sys.stderr)
            record_id=rec["id"]
            record_text=rec["record"][0]
            marc=biblio.Record(record_text)
            #outcome,rec_title=get_title(record_text)
            rec_title=marc.get_title()
            #outcome,author_str=get_author(record_text)
            author_str=marc.get_creator()
            if author_str != "":
               author_str="by "+author_str
#           print("author:", author_str,file=sys.stderr)
            publication_info=marc.get_publication_info()
            title_url=webserver_host+cgi_path+full_record_script+"?id="+str(record_id)
            #title_url='http://localhost/cgi-bin/full_record?id=99400054086'
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
        if search_field != "":
            nextpage_link=webserver_host+cgi_path+'search?query='+quote_user_query+"&search_field="+search_field+'&next='+next_page
        else:
            nextpage_link=webserver_host+cgi_path+'search?query='+quote_user_query+'&next='+next_page
        nextpage_element='<span>  <a href="'+nextpage_link+'" title="Next page"><b>NEXT</b></a>   </span>'
      if int(start_record) - int(page_size) >= 0:
        next_page=str(int(start_record)-int(page_size))
        if search_field != "":
            previouspage_link=webserver_host+cgi_path+'search?query='+quote_user_query+"&search_field="+search_field+'&next='+next_page
        else:
            previouspage_link=webserver_host+cgi_path+'search?query='+quote_user_query+'&next='+next_page
        previouspage_element='<span> <a href="'+previouspage_link+'" title="Previous page"><b>PREVIOUS</b></a>  </span>'

      result_page=re.sub(previous_marker,previouspage_element,result_page)
      result_page=re.sub(next_marker,nextpage_element,result_page)
      in_line=re.compile(r'(.*<input type="text".*?value=")(.*?")(.*?>)(.*)',flags=re.DOTALL)
      user_query=urllib.parse.unquote(user_query,encoding='utf-8')
      m=in_line.match(result_page)
      if m:
           result_page=m.group(1)+user_query+'"'+m.group(3)+m.group(4)
      print_page(result_page)
      return 
# next page: https://euclid/?page=2&q=miles+davis+&search_field=search          
  except HTTPError as http_err:
    print(f'HTTP error occurred: {http_err}',file=sys.stderr)
  except Exception as err:
    print(f'Other error occurred: {err}',file=sys.stderr)
  return

if __name__ == "__main__":
    main() 
