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


  user_query=form["query"].value

# basic safety step
  user_query=re.sub(r'<|>|;|\'|&|:','',user_query)

# normalize query for solr, if needed.
  normalized_q=user_query
  terms=user_query.split(" ")
  boolean_term=False
  normalized_q=""
## make all the terms "required" in the query by using "+" prefix
  for term in terms:
           if term !="":
              term=str(term)
              if term[0] != "+" and term[0] != "-":
                 if str(term) != "OR" and str(term) != "AND" and str(term) != "NOT":
                     normalized_q+="+"+str(term)+" "
                 else:
                     normalized_q+=" "+str(term)+" "
                     boolean_term=True
              else:
                 normalized_q+=str(term)+" "
  temp_q=""
  if boolean_term:
           terms=normalized_q.split(" ")
           for term in terms:
               if term != "":
                   if term[0] == "+" or term[0] == "-":
                       temp_q+=term[1:]+" "
                   else:
                       temp_q+=term+" "
           normalized_q=temp_q

  
  authorized_user,authorized_passwd=credentials.split("_|_")

  process_form(user_query,solr_host,solr_path,form_file,display_results,display_full_record,webserver_host,cgi_path,facet_script,facet_marker,full_record_script,results_marker,next_page,page_size,previous_marker,next_marker,search_script,refine_results,normalized_q,authorized_user,authorized_passwd,record_count_marker)
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



def process_form(user_query,solr_host,solr_path,form_file,display_results,display_full_record,webserver_host,cgi_path,facet_script,facet_marker,full_record_script,results_marker,next_page,page_size,previous_marker,next_marker,search_script,refine_results,normalized_q,authorized_user,authorized_passwd,record_count_marker):
  
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

      if jsonResponse["responseHeader"]["status"]  != 0:
         error_msg=jsonResponse["error"]["msg"]
         print ("solr error ",error_msg, file=sys.stderr)
         print_error("System error(5)")
         return

      number_found=jsonResponse["response"]["numFound"]
      start_record=jsonResponse["response"]["start"]
      record_count=len(jsonResponse["response"]["docs"])
      if record_count == 1 and number_found == 1:
### Only one record found: display full record.
            full_record=displaypage.new_page(display_full_record)
            page_string=full_record.full_page(response,webserver_host,cgi_path,search_script)
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
          spelling=displaypage.new_page(form_file)
          page_string,outcome=spelling.dym_spell(response,user_query,webserver_host,cgi_path,search_script)
          if outcome == 0:
              print_page(page_string)
          else:
              print_error(page_string)
          return
###
###
      multiple_recs=displaypage.new_page(display_results)
      page_string,outcome=multiple_recs.record_list(response,user_query,webserver_host,cgi_path,search_script,refine_results,facet_script,page_size,record_count_marker,facet_marker,previous_marker,next_marker,full_record_script,results_marker)
      if outcome == 0:
            print_page(page_string)
      else:
            print_error(page_string)
      return
  except HTTPError as http_err:
    print(f'HTTP error occurred: {http_err}',file=sys.stderr)
  except Exception as err:
    print(f'Other error occurred: {err}',file=sys.stderr)
  return

if __name__ == "__main__":
    main()
      
