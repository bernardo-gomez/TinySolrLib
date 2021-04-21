#!/usr/bin/env python3

"""
   It receives a query whose target is a solr server.
   The user query targets a specific facet.
       Facet values are static strings, for instance:
           "Davis, Miles." is a facet value for "creator" facet.
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
   It processes a query targeting a specific facet.
   A facet field is defined here as a static string.
   All error messages go to the standard error.
   - If the result contains one record, then it 
   displays the full record.
   - If there are no results, then it's possible
     that solr database is incomplete.
   - If the result contains multiple records, it displays a 
     list of records, along with the corresponding facet list.
  """

  if len(sys.argv) < 2:
       print_error("System error (7)")
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
       print_error("System error (8)")
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
              if m.group(1) == "record_count_marker":
                 record_count_marker=m.group(2)
              if m.group(1) == "facet_marker":
                 facet_marker=m.group(2)
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

  if results_marker == '':
       print("results_marker undefined ",file=sys.stderr)
       failed+=1

  if record_count_marker == '':
       print("record_count_marker undefined ",file=sys.stderr)
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

  if failed > 0:
       print_error("System error (9)")
       return

  if credentials == '':
       print("credentials undefined ",file=sys.stderr)
       failed+=1

  form = cgi.FieldStorage()
  if "q" not in form:
     print_form(form_file)
     return

  if "next" not in form:
     next_page=0
  else:
     next_page=form["next"].value


  filter_query=""
  if "fq" in form:
      filter_query=form["fq"].value
  user_query=form["q"].value
  user_query=re.sub(r'<|>|;|\'','',user_query)
# user_query=re.sub(r'"|,',' ',user_query)

  authorized_user,authorized_passwd=credentials.split("_|_")

  process_form(user_query,solr_host,solr_path,display_results,display_full_record,webserver_host,cgi_path,facet_script,facet_marker,full_record_script,results_marker,next_page,page_size,previous_marker,next_marker,filter_query,refine_results,search_script,authorized_user,authorized_passwd,record_count_marker)
  return

def print_error(message):
     """
         It produces an HTML page with an error message.
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


def process_form(user_query,solr_host,solr_path,display_results,display_full_record,webserver_host,cgi_path,facet_script,facet_marker,full_record_script,results_marker,next_page,page_size,previous_marker,next_marker,filter_query,refine_results,search_script,authorized_user,authorized_passwd,record_count_marker):
  """
    process_form receives the following parameters:
      user_query: as typed by the user;
      solr_host: solr hostname;
      solr_path: a CGI alias, for instance;
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
      filter_query: it holds the value of the designated facet
      search_script: name of cgi script that performs query;
      refine_results: place holder to facet list in HTML page;
      authorized_user: user's name to access solr;
      authorized_passwd: user's password;
   
   This function sends a request containing a designated
   facet to the solr server via API and builds
   a result page after analisying the solr response.

  """
  from requests.auth import HTTPBasicAuth

  next_page=str(next_page)
  page_size=str(page_size)
  fquery=re.compile("(.*?):(.*)")
  m=fquery.match(filter_query)
  filter_q=filter_query
  if m:
      filter_q=m.group(1)+":"+'"'+m.group(2)+'"'
 ### API call
  quote_filter_query=urllib.parse.quote(filter_q)
  try:
      search=solr_host+solr_path+'select?q='+user_query+'&facet=on&facet.field=pubDate&facet.field=language&facet.field=creator&facet.field=contributor&facet.field=genre&facet.field=topic&facet.field=resourceType&fq='+quote_filter_query+'&facet.mincount=1&rows='+page_size+'&start='+next_page
      try:
         response = requests.get(search,auth=HTTPBasicAuth(authorized_user,authorized_passwd),timeout=10)
      except:
         print("connection to solr server failed ",file=sys.stderr)
         print_error("System error(12)")
         return
      if response.status_code != 200:
         if response.status_code  == 401:
             print("connection to solr server failed. Bad credentials. ",file=sys.stderr)
             print_error("System error(22). Bad credentials. ")
             return

         else:
             print("connection to solr server failed.return code:",str(response.status_code),file=sys.stderr)
             print_error("System error(23). ")
             return

      try:
         jsonResponse = response.json()
      except:
         print("connection to solr server failed ",file=sys.stderr)
         print_error("System error(21) not a json response.")
         return

      if jsonResponse["responseHeader"]["status"]  != 0:
         error_msg=jsonResponse["error"]["msg"]
         print ("solr error ",error_msg,file=sys.stderr)
         print_error("System error(10)")
         return

      #print(jsonResponse,file=sys.stderr)

      number_found=jsonResponse["response"]["numFound"]
      start_record=jsonResponse["response"]["start"]
      record_count=len(jsonResponse["response"]["docs"])
      if record_count == 1 and number_found == 1:
 ### result has one record, then show full record.

            record_text=jsonResponse["response"]["docs"][0]["record"][0]
            full_record=displaypage.new_page(display_full_record)
            page_string=full_record.full_page(response,webserver_host,cgi_path,search_script)
            print_page(page_string)
            return
      if record_count == 0:
            print_error("No facet matches. System error(11)")
            print ("No facet matches. Database may be incomplete.",file=sys.stderr)
            return
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
      
