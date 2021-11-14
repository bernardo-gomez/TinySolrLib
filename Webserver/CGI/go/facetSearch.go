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
import "strconv"
import "io/ioutil"
import "net/http/cgi"
import "encoding/json"
import "tinylib/displaypage"
import "tinylib/biblio"

func replaceForm(inPage *regexp.Regexp,pageString string,userQuery string) string{
      line:=strings.Split(pageString,"\n")
      page:=""
      for _,val:= range line {
          result:=inPage.FindStringSubmatch(val)
          if result != nil {
	      page+=result[1]+result[2]+userQuery+result[4]+"\n"
           }  else {
              page+=val+"\n"
           }
      }
      return page
}

func processForm(userQuery string,solrHost string,solrPath string,formFile string,displayResults string,displayFullRecord string,webserverHost string ,cgiPath string,facetScript string,facetMarker string,fullRecordScript string,resultsMarker string,nextPage string,pageSize string,previousMarker string,nextMarker string,filterQuery string,searchScript string,refineResults string,authorizedUser string,authorizedPasswd string,recordCountMarker string) {
	l:=log.New(os.Stderr, "", 0)
        client := &http.Client{
        Timeout: time.Second * 10,
//              Timeout: time.Millisecond * 1,
        }
       terms:=strings.Split(userQuery," ")
       normalizedQ:=""
       for _,term := range terms {
           if term != "" {
                   term=string(term)
                   if (term[0] != '+') && (term[0] != '-') {
                        if (term != "OR") && (term != "AND") && (term != "NOT") {
                           normalizedQ+=" "+"+"+term
                        }
                   } else {
                           normalizedQ+=" "+term+" "
                   }
           }
         }
	quoteUserQuery:=url.QueryEscape(normalizedQ)
	obj1,_ := regexp.Compile(`(.*?):(.*)`)
	fqQuery:=obj1.FindStringSubmatch(filterQuery)
	filterQ:=""
	quoteFilterQuery:=""
	if len(fqQuery) > 2 {
		filterQ=fqQuery[1]+":"+`"`+fqQuery[2]+`"`
        } else {
	        filterQ=filterQuery
	}
	quoteFilterQuery=url.QueryEscape(filterQ)
	
  	reqUrl:=solrHost+solrPath+"select?q="+quoteUserQuery+"&facet=true"+"&fq="+quoteFilterQuery+"&facet.field=language&facet.field=contributor&facet.field=pubDate&facet.field=resourceType&facet.field=topic&facet.field=genre&facet.mincount=1&rows="+pageSize+"&start="+nextPage
        method:="GET"
        req, err := http.NewRequest(method, reqUrl, nil)
        if err != nil {
                fmt.Printf("error type: %T\n", err)
                fmt.Printf("error value: %v\n", err)
                log.Fatal("Error reading response. ", err)
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
	numFoundStr:=strconv.FormatFloat(numFound, 'f', -1, 64)
	startRecord:=jresponse["start"].(float64)
	jdocs,ok:=jresponse["docs"].([] interface{})
	if !ok {
   	     l.Println("solr didn't return docs")
  	     printError("FAILED docs!")
   	     return
	}
	recordCount:=len(jdocs)

	if recordCount == 1  && numFound == 1{
            fullRec:=displaypage.New(displayFullRecord)
	    pageString,err:=fullRec.FullPage(body,webserverHost,cgiPath,searchScript)
	    if err == nil {
		    printPage(pageString)
		    return
	    } else {
  	          printError("Full record display failed")
	    }
	}

	if recordCount == 0{

	   file,err:=os.Open(formFile)
           if err != nil {
                log.Fatal("Error opening file. ", err)
                printError("System error(32).")
                return 
           }
           defer file.Close()
	   pageString:=""
           scanner := bufio.NewScanner(file)
           for scanner.Scan() {
                pageString+=scanner.Text()+"\n"
           }

           method:="GET"
	   quotedQuery:=url.QueryEscape(userQuery)
	   url:=solrHost+solrPath+"spell?spellcheck.q="+quotedQuery+"&spellcheck=on"
           req, err := http.NewRequest(method, url, nil)
           if err != nil {
                //fmt.Printf("error type: %T\n", err)
                //fmt.Printf("error value: %v\n", err)
                log.Fatal("Error reading response. ", err)
                printError("System error(26). NewRequest() failed.")
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
	   var jbody map[string] interface{}
	   err1:=json.Unmarshal(body,&jbody)
	   if err1 != nil {
               printError("System error(30). Not a json response.")
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
	   jSpellCheck,ok:=jbody["spellcheck"].(map[string] interface{})
	   if !ok {
  	        printError("FAILED jresponse!")
		return
	   }
	   jCollations,ok:=jSpellCheck["collations"].([]  interface{})
	   if len(jCollations) == 0 {
		noResults:=`<div><h2>No Results Found</h2></div>`
	        pageString=strings.Replace(pageString,"<!--NORESULTS=-->",noResults,-1)
	        inLine,err:=regexp.Compile(`(.*<input type="text".*?value=")(.*?)(.*?)(.*)`)
	        if err != nil {
	            l.Println("regexp compile failed",err)
  	            printError("System error(35)")
		    return 
	        }
		pageString=replaceForm(inLine,pageString,userQuery)
	        printPage(pageString)
		return
	   }
           collation:=jCollations[1].(map[string] interface{})
	   suggested:=collation["collationQuery"].(string)
	   searchURI:=webserverHost+cgiPath+searchScript+"?query="+suggested
           didYouMean:=`<div><span><h2>Did you mean <a href="`+searchURI+`">`+suggested+`</a>?</h2></span></div>`
	   pageString=strings.Replace(pageString,"<!--DIDYOUMEAN=-->",didYouMean,-1)
	   inLine,err:=regexp.Compile(`(.*<input type="text".*?value=")(.*?)(.*?)(.*)`)
	   if err != nil {
	       l.Println("regexp compile failed",err)
  	       printError("System error(37)")
	       return
	   }
	   pageString=replaceForm(inLine,pageString,userQuery)
	   printPage(pageString)
	   return
        }
	// display multiple results
	refineResultString:=""
        data,err:=ioutil.ReadFile(refineResults)
	if err != nil {
	       l.Println("open failed",err)
  	       printError("System error(38)")
	       return
        }
        refineResultString=string(data)
	facetInfo,ok:=jbody["facet_counts"].(map[string] interface{})
	if !ok {
	       l.Println("json response doesn't have facet_counts")
  	       printError("System error(39)")
	       return
	}
	facetFields,ok:=facetInfo["facet_fields"].(map[string] interface{})
	if !ok {
	       l.Println("facet_counts doesn't have facet_fields")
  	       printError("System error(40)")
	       return
	}
// "facet_counts":{
//  "facet_queries":{},
//  "facet_fields":{
//    "pubDate":[
//      "1989",2,
//      "2004",2,
//      "1994",1,
//    "language":[
//      "english",5,
//      "chinese",1]},
//  "facet_ranges":{},
//  "facet_intervals":{},
//  "facet_heatmaps":{}}

	facets:=make(map[string] []string)
	var itemList[] string
	for fname,fList:= range facetFields {
           fvalue,ok:=fList.([] interface {})
	   if !ok {
	       l.Println("error retrieving facet names")
  	       printError("System error(42)")
	       return
	   }
	   state:="get_item"
	   ivalue:=""
	   icount:=0.0
	   itemList=[]string{}
	   for _,v := range fvalue {
		if state == "get_item" {
		   ivalue=v.(string)
		   state="get_count"
		} else {
		   icount=v.(float64)
		   s64:=strconv.FormatFloat(icount, 'f', -1, 64)
		   is:=ivalue+"_|_"+s64
		   itemList=append(itemList,is)
		   state="get_item"
		}
	   }
           facets[fname]=itemList
	}
        reqList:=""
	htmlMarker:=""
	var instance []string
	instanceValue:=""
	instanceCount:=""
	for key,ivalue:= range facets {
	    htmlMarker="<!--"+key+"=-->"
	    for _,iv:= range ivalue {
		   instance=strings.Split(iv,"_|_")
		   if len(instance) == 2{
		       instanceValue=instance[0]
		       instanceCount=instance[1]
	               quoteUserQuery:=url.QueryEscape(userQuery)
	               quoteInstanceValue:=url.QueryEscape(instanceValue)
		       facetQueryReq:="&q="+quoteUserQuery+"&fq="+key+":"+quoteInstanceValue
		       facetRequest:=webserverHost+cgiPath+facetScript+"?"+facetQueryReq
		       spanE:=`<li><span><a href="`+facetRequest+`">`+instanceValue+`</a>`+`</span>`+`<span>`+" "+instanceCount+`</span>`+"</li>"
		       reqList+=spanE
		   }
            }
	    refineResultString=strings.Replace(refineResultString,htmlMarker,reqList,-1)
	    reqList=""
	}
	resultPage:=""
        data,err=ioutil.ReadFile(displayResults)
	if err != nil {
	       l.Println("open failed",err)
  	       printError("System error(38)")
	       return
        }
//	"facet_counts":{
//  "facet_queries":{
//    "language:English":6},
//  "facet_fields":{
//    "language":[
//     "English",6,
//        "Unknown",2,
//        "Arabic",0,
//        "Chinese",0]},
//    "facet_ranges":{},
//    "facet_intervals":{},
//    "facet_heatmaps":{}}

        resultPage=string(data)
	resultPage=strings.Replace(resultPage,facetMarker,refineResultString,-1)
        resultCount:=`Number of records:`+numFoundStr
	resultCount=`<h3>`+resultCount+`</h3>`
	resultPage=strings.Replace(resultPage,recordCountMarker,resultCount,-1)
//  	printError("Under construction")
        recordTable:=""
	recordTable=`<div class="RecResults">`
	recordTable+=`<table class="RecordTable">`
	for _,docs:= range jdocs {
            rec:=docs.(map[string] interface{})
	    recordTxt:=rec["record"].([] interface{})
	    marcText:=recordTxt[0].(string)
	    marc:=biblio.New(marcText)
	    title:=marc.GetTitle()
	    authorStr:=marc.GetCreator()
	    if authorStr != "" {
		    authorStr="by "+authorStr
	    }
	    publicationInfo:=marc.GetPublicationInfo()
	    recordID:=marc.GetRecordID()
	    titleURL:=webserverHost+cgiPath+fullRecordScript+`?id=`+recordID
	    recordTable+=`<tr>`
	    recordTable+=`<td>`
            recordTable+=`<div class="SummaryFields">`
            recordTable+=`<h2>`
            recordTable+=`<a href="`+titleURL+`">`+title+`</a>`
            recordTable+=`</h2>`
	    if authorStr != ""{
		 recordTable+=`<h3>`+authorStr+`</h3>`
	    }
	    recordTable+=`<h3>`+publicationInfo+`</h3>`
	    recordTable+=`</div>`
            recordTable+=`</td>`
            recordTable+=`</tr>`
	}
	recordTable+=`</tbody>`
        recordTable+=`</table>`
        recordTable+=`</div>`
	resultPage=strings.Replace(resultPage,resultsMarker,recordTable,-1)
        nextPageLink:=""
        previousPageLink:=""
	nextPageElement:=""
	previousPageElement:=""
	startRecordInt:=int64(startRecord)
	pageSizeInt,err2:=strconv.Atoi(pageSize)
	if err2 != nil {
           printError("Page size conversion failed.")
	   return
	}
	numFoundInt:=int64(numFound)
//	if int(start_record) + int(page_size) < int(number_found):
        if startRecordInt + int64(pageSizeInt) <  numFoundInt {
	    nextPageInt:=startRecordInt + int64(pageSizeInt)
	    quotedQuery:=url.QueryEscape(userQuery)
	    nextPageStr:=strconv.FormatInt(nextPageInt,10)
// http://localhost/cgi-bin/facet_search?&q=miles%20davis&facet.field=language&fq=language:English
	    facetRequest:=webserverHost+cgiPath+facetScript+"?q="+quotedQuery+"&fq="+filterQuery
	    nextPageLink=facetRequest+"&next="+nextPageStr
	    nextPageElement=`<span>  <a href="`+nextPageLink+`" title="Next page"><b>NEXT</b></a>  </span>`
        }
	if startRecordInt - int64(pageSizeInt) >= 0 {
		 nextPageInt:=startRecordInt-int64(pageSizeInt)
	         nextPageStr:=strconv.FormatInt(nextPageInt,10)
	         quotedQuery:=url.QueryEscape(userQuery)
	         facetRequest:=webserverHost+cgiPath+facetScript+"?q="+quotedQuery+"&fq="+filterQuery
		 previousPageLink=facetRequest+"&next="+nextPageStr
		 previousPageElement=`<span>  <a href="`+previousPageLink+`" title="Previous page"><b>PREVIOUS</b></a>  </span>`
        }
	resultPage=strings.Replace(resultPage,previousMarker,previousPageElement,-1)
	resultPage=strings.Replace(resultPage,nextMarker,nextPageElement,-1)
	inLine,err:=regexp.Compile(`(.*<input type="text".*?value=")(.*?)(.*?)(.*)`)
	if err != nil {
	         l.Println("regexp compile failed",err)
  	         printError("System error(35)")
	         return 
	}
        resultPage=replaceForm(inLine,resultPage,userQuery)
        printPage(resultPage)
	return

}
func printPage(resultPage string){
    fmt.Println("Content-Type: text/html")    
    fmt.Println("") 
    fmt.Println(resultPage)
    return
}

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
func main() {
   l := log.New(os.Stderr, "", 0)
   argLength := len(os.Args[1:])
   if argLength == 0 {
      printError("Not ready yet")
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
   //var param[] string
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
            //  if m.group(1) == "display_results":
            //     display_results=m.group(2)
            //  if m.group(1) == "form_file":
            //     form_file=m.group(2)

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
   if failed > 0 {
          printError("System error(7)")
          os.Exit(0)
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
   userQuery:=req.Form.Get("q")
   nextPage:=req.Form.Get("next")
   filterQuery:=req.Form.Get("fq")
   if userQuery == "" {
	 printForm(formFile)
	 os.Exit(0)
   }
   if nextPage == "" {
	   nextPage="0"
   }
   subs,err:=regexp.Compile(`<|>|;|'|&|:`)
   userQuery=subs.ReplaceAllString(userQuery,"")
   authorization:=strings.Split(credentials,"_|_")
   authorizedUser:=authorization[0]
   authorizedPasswd:=authorization[1]
   processForm(userQuery,solrHost,solrPath,formFile,displayResults,displayFullRecord,webserverHost,cgiPath,facetScript,facetMarker,fullRecordScript,resultsMarker,nextPage,pageSize,previousMarker,nextMarker,filterQuery,searchScript,refineResults,authorizedUser,authorizedPasswd,recordCountMarker)

}
