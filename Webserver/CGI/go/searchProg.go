package main
import "fmt"
import "log"
import "strings"
import "os"
import "bufio"
import "net/http"
import "net/url"
import "regexp"
import "time"
import "io/ioutil"
import "net/http/cgi"
import "encoding/json"
import "tinylib/displaypage"


// processForm receives the necessary information from the client 
// to submit the query to the solr server. It returns the html page to the
// client with the result.
// processForm receives:
// userQuery: the user query,
// solrHost: the solr hostname,
// solrPath: the solr http path,
// formFile: the file with the search form,
// displayResults: the file with the html page to display results,
// displayFullRecord: the file with the html page to display the full record,
// webserverHost: the webserver host name,
// cgiPath: the webserver's CGI path,
// facetScript: the name of facet script,
// facetMarker: the facet holder in the html page,
// fullRecordScript: the name of the script that builds the full record,
// resultsMarker: the marker for displaying list of records in the html page,
// nextPage: the record number that starts the next page,
// pageSize: the number of results to display in each page,
// previousMarker:the previous page marker in the html page,
// nextMarker: the next page marker in the html page,
// searchScript: the name of the CGI script that performs a general solr search,
// refineResults: the file that holds the facet template,
// normalizedQ: the normalized query according to MARC conventions,
// authorizedUser: the user name for solr authorization,
// authorizedPasswd: the password for solr authorization,
// recordCountMarker: the holder of the record count in the result page.
func processForm(userQuery string,solrHost string,solrPath string,formFile string,displayResults string,displayFullRecord string,webserverHost string ,cgiPath string,facetScript string,facetMarker string,fullRecordScript string,resultsMarker string,nextPage string,pageSize string,previousMarker string,nextMarker string,searchScript string,refineResults string,normalizedQ string,authorizedUser string,authorizedPasswd string,recordCountMarker string) {
	l:=log.New(os.Stderr, "", 0)
	var query string = ""
        client := &http.Client{
        Timeout: time.Second * 10,
        }
	quoteUserQuery:=url.QueryEscape(normalizedQ)
	query=quoteUserQuery
	reqUrl:=solrHost+solrPath+"select?q="+query+"&facet=true&facet.field=pubDate&&facet.field=language&facet.field=resourceType&facet.field=topic&facet.field=genre&facet.field=creator&facet.field=contributor&facet.mincount=1&rows="+pageSize+"&start="+nextPage
        method:="GET"
        req, err := http.NewRequest(method, reqUrl, nil)
        if err != nil {
                l.Println("Error reading response. ", err)
                printError("System error(26). NewRequest() failed.")
        }
        req.Header.Set("Cache-Control", "no-cache")
        req.Header.Set("Content-Type", "application/json")
        req.SetBasicAuth(authorizedUser, authorizedPasswd)
        response, err := client.Do(req)
	if err != nil {
	      l.Println("connection to solr server failed.",err)
              printError("System error(23). request to solr failed.")
	      return 
	}
	if response.Status != "200 OK" {
	   if response.Status == "401" {
	      l.Println("connection to solr server failed. Bad credentials.")
              printError("System error(22). Bad credentials.")
	      return 
           } else {
	      l.Println("response status:",response.Status)
              printError("System error(24)")
   	      return
           }
	}

  	body, err := ioutil.ReadAll(response.Body)
	var jbody map[string] interface{}
	err1:=json.Unmarshal(body,&jbody)
	if err1 != nil {
             printError("System error(25). Not a json response.")
	     l.Println("couldn't parse json response")
	     return 
        }
	header,ok:=jbody["responseHeader"].(map[string] interface{})
        if !ok   {
  	        printError("Error. couldn't parse json response.")
		return
	}
	if header["status"].(float64) != 0 {
  		l.Println("status:",header["status"],)
  	        printError("Error. solr invalid request")
		return
	}
	jresponse,ok:=jbody["response"].(map[string] interface{})
	if !ok {
  	        printError("FAILED jresponse!")
		return
	}
	numFound:=jresponse["numFound"].(float64)
	jdocs,ok:=jresponse["docs"].([] interface{})
	if !ok {
   	     l.Println("solr didn't return docs")
  	     printError("FAILED docs!")
   	     return
	}
	recordCount:=len(jdocs)

	if recordCount == 1 && numFound == 1{
            fullRec:=displaypage.New(displayFullRecord)
	    pageString,err:=fullRec.FullPage(body,webserverHost,cgiPath,searchScript)
	    if err == nil {
		    printPage(pageString)
		    return
	    } else {
  	          printError("Full record display failed")
		  return
	    }
	}

	if recordCount == 0{

//	   file,err:=os.Open(formFile)
//           if err != nil {
//                l.Println("Error opening file. ", err)
//                printError("System error(32).")
//                return 
//           }
//           defer file.Close()
//	   pageString:=""
//           scanner := bufio.NewScanner(file)
//           for scanner.Scan() {
//                pageString+=scanner.Text()+"\n"
//           }

           method:="GET"
	   quotedQuery:=url.QueryEscape(userQuery)
	   url:=solrHost+solrPath+"spell?spellcheck.q="+quotedQuery+"&spellcheck=on"
           req, err := http.NewRequest(method, url, nil)
           if err != nil {
                l.Println("Error reading response. ", err)
                printError("System error(26). NewRequest() failed.")
		return
	   }
           req.Header.Set("Cache-Control", "no-cache")
           req.Header.Set("Content-Type", "application/json")
           req.SetBasicAuth(authorizedUser, authorizedPasswd)
           response, err := client.Do(req)
	   if err != nil {
	        l.Println("connection to solr server failed.",err)
                printError("System error(23). spell request to solr failed.")
	        return 
	   }
	   if response.Status != "200 OK" {
	     if response.Status == "401" {
	        l.Println("connection to solr server failed. Bad credentials.")
                printError("System error(28). Bad credentials.")
	        return 
             } else {
	        l.Println("spell response status:",response.Status)
                printError("System error(29)")
   	        return
             }
	   }
  	   body, err := ioutil.ReadAll(response.Body)

            zeroRecs:=displaypage.New(formFile)
	   didYouMeanPage,DYMerror:=zeroRecs.DidYouMean(body,userQuery,webserverHost ,cgiPath,searchScript)
	   if DYMerror == nil {
	     printPage(didYouMeanPage)
	   } else{
	      printError(didYouMeanPage)
           }
	   return
        }
//	MultipleRecs(jsonSolr []byte, userQuery string, webserverHost string, cgiPath string, searchScript string, refineResults string, facetScript string, facetMarker string, recordCountMarker string, fullRecordScript string, resultsMarker string, pageSize string,  previousMarker string, nextMarker string)
	// display multiple results
  	recList:=displaypage.New(displayResults)
  	pageString,outcome:=recList.MultipleRecs(body, userQuery, webserverHost, cgiPath, searchScript, refineResults, facetScript, facetMarker, recordCountMarker, fullRecordScript , resultsMarker , pageSize,  previousMarker, nextMarker)
       if outcome == nil{
	       printPage(pageString)
       } else {
	       printError(pageString)
       }
       return
}

// printPage writes to standard ouput (response to client) the
// html string. 
// printPage receives:
// resultPage: html string
// printPage returns nothing
func printPage(resultPage string){
    fmt.Println("Content-Type: text/html")    
    fmt.Println("") 
    fmt.Println(resultPage)
    return
}

// printForm writes the content of an html file standard output.
// printForm receives:
// formFile: html file with a search box.
// printForm returns nothing
func printForm(formFile string) {

    fmt.Println("Content-Type: text/html")   
    fmt.Println("")  
    data, err := ioutil.ReadFile(formFile)
    if err != nil {
       printError("System error(2)")
       return
    }
    fmt.Printf(string(data))
    return
}
// printError writes to standard output a message. 
// printError receives a string that serves as an html message.
func printError(message string) {
     fmt.Println("Content-Type: text/html")   
     fmt.Println("") 
     fmt.Println("<!DOCTYPE html>")
     fmt.Println("<html lang=\"en-US\">")
     fmt.Println("<head>")
     fmt.Println("<title>Error</title>")
     fmt.Println("<meta charset=\"utf-8\">")
     fmt.Println("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">")
     fmt.Println("</head>")
     fmt.Println("<body>")
     fmt.Println("<H1>",message,"</H1>")
     fmt.Println("</body>")
     fmt.Println("</html>")
     return
}

// This program is part of an webserver that processes a user search
// against a Solr repository. The solr records are based on MARC records.
// To run the program issue: searchProg config-file.
// The program receives the user query via an html form.
//  The result of the query could be:
//    - No matches. In this case the program issues a spell request
//        to Solr.
//    - A single match. In this case the program displays the full 
//        record.
//    - Multiple matches. In this case the program displays up
//       to a given number of records in brief format.
//   The program returns an html page to the http client.
func main() {
   l := log.New(os.Stderr, "", 0)
   argLength := len(os.Args[1:])
   if argLength == 0 {
      printError("System error. Configuration file is missing.")
      os.Exit(0)
   }
   _,err := os.Stat(os.Args[1])
   if os.IsNotExist(err) {
       printError("System error")
       l.Println(err)
       os.Exit(0)
   }
   file,err:=os.Open(os.Args[1])
   if err != nil {
       printError("System error(2)")
       os.Exit(0)
   }
   defer file.Close()
   scanner := bufio.NewScanner(file)
   scanner.Split(bufio.ScanLines)
   reConf,err:=regexp.Compile(`(.*?)=(.*)`)
   if err != nil {
       printError("System error(3)")
       os.Exit(0)
   }
   
     var solrHost=""
     var solrPath=""
     var webserverHost=""
     var cgiPath=""
     var searchScript=""
     var facetScript=""
     var fullRecordScript=""
     var displayFullRecord=""
     var displayResults=""
     var formFile=""
     var refineResults=""
     var facetMarker=""
     var recordCountMarker=""
     var resultsMarker=""
     var previousMarker=""
     var nextMarker=""
     var pageSize=""
     var credentials=""
     failed:=0

   for scanner.Scan(){
      line:=scanner.Text()
      result:=reConf.FindStringSubmatch(line)
      if len(result)  < 1 {
         printError("System error(4)")
         os.Exit(0)
      }

      if  result[1] == "solr_host" {
          solrHost=result[2]
      }
      if result[1] == "solr_path" {
          solrPath=result[2]
      }
      if result[1] == "webserver_host" {
          webserverHost=result[2]
      }
      if result[1] == "cgi_path" {
          cgiPath=result[2]
      }
      if result[1] == "search_script" {
          searchScript=result[2]
      }
      if result[1] == "facet_script" {
          facetScript=result[2]
      }
      if result[1] == "full_record_script" {
          fullRecordScript=result[2]
      }
      if result[1] == "display_full_record" {
          displayFullRecord=result[2]
      }
      if result[1] == "display_results" {
          displayResults=result[2]
      }
      if result[1] == "form_file" {
          formFile=result[2]
      }
      if result[1] == "credentials" {
          credentials=result[2]
      }
      if result[1] == "refine_results" {
          refineResults=result[2]
      }
      if result[1] == "facet_marker" {
          facetMarker=result[2]
      }
      if result[1] == "record_count_marker" {
          recordCountMarker=result[2]
      }
      if result[1] == "results_marker" {
          resultsMarker=result[2]
      }
      if result[1] == "previous_marker" {
          previousMarker=result[2]
      }
      if result[1] == "next_marker" {
          nextMarker=result[2]
      }
      if result[1] == "page_size" {
          pageSize=result[2]
      }

   }
   if solrHost == "" {
         failed+=1
         l.Println("config param solr_host undefined")
   }
   if solrPath == "" {
         failed+=1
         l.Println("config param solr_path undefined")
   }
   if webserverHost  == "" {
         failed+=1
         l.Println("config param webserver_host  undefined")
   }
   if cgiPath  == "" {
         failed+=1
         l.Println("config param cgi_path  undefined")
   }
   if searchScript  == "" {
         failed+=1
         l.Println("config param search_script undefined")
   }
   if facetScript  == "" {
         failed+=1
         l.Println("config param facet_script undefined")
   }
   if fullRecordScript  == "" {
         failed+=1
         l.Println("config param full_record_script undefined")
   }
   if displayFullRecord  == "" {
         failed+=1
         l.Println("config param display_full_record undefined")
   }
   if displayResults  == "" {
         failed+=1
         l.Println("config param display_results undefined")
   }
   if formFile  == "" {
         failed+=1
         l.Println("form_file undefined")
   }
   if credentials  == "" {
         failed+=1
         l.Println("credentials undefined")
   }
   if refineResults  == "" {
         failed+=1
         l.Println("refine_results undefined")
   }
   if facetMarker  == "" {
         failed+=1
         l.Println("facet_marker undefined")
   }
   if recordCountMarker == "" {
         failed+=1
         l.Println("record_count_marker undefined")
   }
   if resultsMarker == "" {
         failed+=1
         l.Println("results_marker undefined")
   }
   if previousMarker == "" {
         failed+=1
         l.Println("previous_marker undefined")
   }
   if nextMarker == "" {
         failed+=1
         l.Println("next_marker undefined")
   }
   if pageSize == "" {
         failed+=1
         l.Println("page_size undefined")
   }

   if failed > 0 {
          printError("System error. Configuration file incomplete.")
          os.Exit(0)
   }
   req,err:=cgi.Request()
   if err != nil {
          printError("Request failed")
          os.Exit(0)
   }
   err=req.ParseForm()
   if err != nil {
          printError("ParseForm failed")
          os.Exit(0)
   }
   if len(req.Form) == 0 {
	   printForm(formFile)
	   os.Exit(0)
   }
   userQuery:=req.Form.Get("query")
   nextPage:=req.Form.Get("next")
   if userQuery == "" {
	 printForm(formFile)
	 os.Exit(0)
   }
   if nextPage == "" {
	   nextPage="0"
   }
   var normalizedQ string =""
   subs,err:=regexp.Compile(`<|>|;|'|&`)   // play safe with shell chars.
   userQuery=subs.ReplaceAllString(userQuery,"") //xxxxx
   normalizedQ=userQuery
   terms:=strings.Split(userQuery," ")
   var booleanTerm bool =false
	 normalizedQ=""
	 for _,term := range terms {
           if term != "" {
		   term=string(term)
		   if (term[0] != '+') && (term[0] != '-') {
			if (term != "OR") && (term != "AND") && (term != "NOT") {
			   normalizedQ+=" "+"+"+term
			} else {
			   normalizedQ+=" "+term+" "
			   booleanTerm=true
		        }
		   } else {
			   normalizedQ+=" "+term+" "
		   }
           }
	 }
	 tempQ:=""
	 if booleanTerm {
             terms:=strings.Split(normalizedQ," ")
	     for _,term := range terms {
		  if term != ""{
		      if (term[0] == '+') || (term[0] == '-') {
				 tempQ+=term[1:] + " "
		      }  else {
			      tempQ+=term+" "
		      }
		  }
	     }
	     normalizedQ=tempQ
         }
   authorization:=strings.Split(credentials,"_|_")
   authorizedUser:=authorization[0]
   authorizedPasswd:=authorization[1]
   processForm(userQuery,solrHost,solrPath,formFile,displayResults,displayFullRecord,webserverHost,cgiPath,facetScript,facetMarker,fullRecordScript,resultsMarker,nextPage,pageSize,previousMarker,nextMarker,searchScript,refineResults,normalizedQ,authorizedUser,authorizedPasswd,recordCountMarker)

}
