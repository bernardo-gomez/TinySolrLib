#!/usr/bin/env python3
"""
   It receives a record ID from a web client;
     it searches record in solr via solr's API  and
     it displays the full record.
"""
__author__= 'bernardo gomez'
__date__ = 'september 2020'



import requests
from requests.exceptions import HTTPError

import json
import sys
import os 
import cgi
from pathlib import Path
import re
import displaypage
import urllib.parse
import cgitb
import biblio
cgitb.enable()


def main():
  """
   It expects a configuration file on the command line.
   All error messages go to the standard error.

  """
  if len(sys.argv) < 2:
       print_error("System error (15)")
       print("No configuration file",file=sys.stderr)
       return

  cfg_file=sys.argv[1]

 # retrieve configuration variables.
  solr_host=""
  solr_path=""
  webserver_host=""
  cgi_path=""
  search_script=""
  full_record_script=""
  display_full_record=""
  form_file=""
  credentials=""

  failed=0
  if not Path(cfg_file).exists():
       print_error("System error(16)")
       failed+=1
       print("configuration file doesn't exist",file=sys.stderr)
       return 

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
              if m.group(1) == "full_record_script":
                 full_record_script=m.group(2)
              if m.group(1) == "display_full_record":
                 display_full_record=m.group(2)
              if m.group(1) == "form_file":
                 form_file=m.group(2)
              if m.group(1) == "credentials":
                 credentials=m.group(2)

  if not Path(display_full_record).exists():
       failed+=1
       print(display_full_record, " not found",file=sys.stderr)

  if not Path(form_file).exists():
       print(form_file, " not found",file=sys.stderr)
       failed+=1

  if search_script == '':
       failed+=1
       print("search_script undefined ",file=sys.stderr)

  if credentials == '':
       print("credentials undefined ",file=sys.stderr)
       failed+=1

  if failed > 0:
       print_error("System error(17)")
       print("One or more configuration variables are undefined. Suggestion: revise configuration file.",file=sys.stderr)
       return

######

##
  form = cgi.FieldStorage()
  if "id" not in form:
     print_form(form_file)
     return

  mms_id=form["id"].value

### record id must be an integer.
  test_input=str(mms_id)
  if not test_input.isnumeric(): 
          print_error("invalid request")
          print("Record ID is not an integer.",file=sys.stderr)
          return

  authorized_user,authorized_passwd=credentials.split("_|_")

  process_req(solr_host,solr_path,display_full_record,webserver_host,cgi_path,search_script,mms_id,authorized_user,authorized_passwd)
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



def process_req(solr_host,solr_path,display_full_record,webserver_host,cgi_path,search_script,mms_id,authorized_user,authorized_passwd):

  """
    input parameters:
     - solr_host: solr hostname;
     - solr_path: a CGI alias;
     - display_full_record: file that serves as an HTML template;
     - webserver_host: hostname of the webserver that hosts these scripts;
     - cgi_path: cgi directory for these scripts;
     - search_script: name of cgi script that performs query;
     - mms_id: ALMA bibliographic record ID;
     - authorized_user: solr's user name;
     - authorized_passwd: user's password;

  """
  from requests.auth import HTTPBasicAuth

 ## solr API call
  try:
      search=solr_host+solr_path+'select?q=id:'+str(mms_id)
      try:
         response = requests.get(search,auth=HTTPBasicAuth(authorized_user,authorized_passwd),timeout=10)
         jsonResponse = response.json()
      except:
         print("connection to solr server failed ",file=sys.stderr)
         print_error("System error(19)")
         return


      if jsonResponse["responseHeader"]["status"]  != 0:
         error_msg=jsonResponse["error"]["msg"]
         print ("solr error ",error_msg,file=sys.stderr)
         print_error("System error(20)")
         return

# open full-record html file.
      full_rec_string=""
      with open(display_full_record) as f:
         for line in f:
            full_rec_string+=str(line)

      number_found=jsonResponse["response"]["numFound"]
      start_record=jsonResponse["response"]["start"]
       #print(len(jsonResponse["response"]["docs"]))
      record_count=len(jsonResponse["response"]["docs"])
      if record_count == 1:
### invoke displaypage class.
            full_record=displaypage.fullRecord(display_full_record)
###
##   displaying user query might create confusion here
            user_query=""
###
            page_string=full_record.full_page(jsonResponse,user_query,webserver_host,cgi_path,search_script)
            print_page(page_string)
            return

      if record_count == 0:
            print_error("Record not found.")
            print("record not found in solr:",str(mms_id),file=sys.stderr)
            return
  except HTTPError as http_err:
    print(f'HTTP error occurred: {http_err}',file=sys.stderr)
  except Exception as err:
    print(f'Other error occurred: {err}',file=sys.stderr)
  return

if __name__ == "__main__":
    main()
