// package displaypage builds an html string
package displaypage

import (
        "os"
        "bufio"
        "log"
  	"encoding/json"
  	"net/url"
	"errors"
	"strings"
	"regexp"
	"tinylib/biblio"
	"strconv"
        "io/ioutil"
)

type htmlPage  struct { 
    serverPage string    
}

// New receives a file with an html template and 
//   creates a corresponding html string.
func New(htmlFile string) htmlPage {
    var page htmlPage
    file,err:=os.Open(htmlFile)
    if err != nil {
        return  page
    }
    defer file.Close()
    page.serverPage=""
    scanner := bufio.NewScanner(file)
    for scanner.Scan() {
	page.serverPage+=scanner.Text()+"\n"
    }
    return page
}
// full_page builds the html page that displays a single record.
//      full_page receives 
//          jsonSolr: the solr description of the record,
//          webserverHost: host name of the search platform,
//          cgiPath: CGI path,
//          search_script: CGI script that performs generic search
//       full_page returns the html string and an error object.
//                error == nil, then success
//                error != nil, then failure.
func (page *htmlPage) FullPage(jsonSolr []byte, webserverHost string, cgiPath string, searchScript string) (string, error) {
     pageString:=""
     userQuery:=""
     l:=log.New(os.Stderr, "", 0)
     var jResponse map[string] interface{}
     err1:=json.Unmarshal(jsonSolr,&jResponse)
     if err1 != nil {
          return pageString,errors.New("Invalid json object")
     }
     jresponse,ok:=jResponse["response"].(map[string] interface{})
     if ! ok {
          return pageString,errors.New("Invalid json object")
     }
     jdocs,ok:=jresponse["docs"].([] interface{})
     if !ok {
          l.Println("solr didn't return docs")
          return pageString,errors.New("Invalid json object")
     }

     if len(jdocs) == 0 {
	    return pageString,errors.New("Marc record missing in json object.")
     }
     docList,ok:=jdocs[0].(map[string] interface {})
     if !ok {
          l.Println("solr didn't return docs")
          return pageString,errors.New("Invalid json object")
     }
     recordT,ok:=docList["record"].([] interface {})
     recordText:=recordT[0].(string)
     onlineAccess:=""
     authorityID:=""
     authorityName,ok:=docList["loc_authority_name"].([] interface {})
     if  ok {
	     authorityID=authorityName[0].(string)
     }
     marc:=biblio.New(recordText)
     title:=marc.GetTitle()
     creator:=marc.GetCreator()
     contributor:=marc.GetContributor()
     genre:=marc.GetGenre()
     topic:=marc.GetTopic()
     oclcString:=marc.GetOclcString()
     onlineAccess=marc.GetURL()
     pageString=page.serverPage
     pageString=strings.Replace(pageString,"<!--TITLE=-->",title,-1)
     if creator != "" {
	userQuery="\""+creator+"\""
	quoteUserQuery:=url.QueryEscape(userQuery)
	searchUrl:=webserverHost+cgiPath+searchScript+"?query="+quoteUserQuery+"&fq=creator:"+quoteUserQuery
	mainAuthor:="<tr><th>Main Author:</th><td><span><a href=\""+searchUrl+"\">"+creator+"</a></span></td></tr>" 
	pageString=strings.Replace(pageString,"<!--MAIN_AUTHOR=-->",mainAuthor,-1)
     }
     if len(contributor) > 0  {
           contribList:="<tr><th>Contributors:</th><td>"
	  for _,thisContrib:= range contributor {
	      quoteUserQuery:="\""+thisContrib+"\""
	      quoteUserQuery=url.QueryEscape(quoteUserQuery)
	      searchUrl:=webserverHost+cgiPath+searchScript+"?query="+quoteUserQuery+"&fq=contributor:"+quoteUserQuery
              item:="<div><a href=\""+searchUrl+"\">"+thisContrib+"</a></div>"
              contribList+=item
	  }
          contribList=contribList+"</td></tr>"
          pageString=strings.Replace(pageString,"<!--OTHER_AUTHORS=-->",contribList,-1)
     }

     if len(genre) + len(topic) > 0 {
	     query:=""
	     subjectList:="<tr><th>Subject:</th><td>"
	     for _,gItem := range genre {
		     query="\""+gItem+"\""
		     quoteQuery:=url.QueryEscape(query)
		     searchUrl:=webserverHost+cgiPath+searchScript+"?query="+quoteQuery+"&fq=genre:"+quoteQuery
		     item:="<div><a href=\""+searchUrl+"\">"+gItem+"</a></div>"
		     subjectList+=item
	     }
	     for _,tItem := range topic {
		     query="\""+tItem+"\""
		     quoteQuery:=url.QueryEscape(query)
		     searchUrl:=webserverHost+cgiPath+searchScript+"?query="+quoteQuery+"&fq=topic:"+quoteQuery
		     item:="<div><a href=\""+searchUrl+"\">"+tItem+"</a></div>"
		     subjectList+=item
	     }
	     subjectList=subjectList+"</td></tr>"
	     pageString=strings.Replace(pageString,"<!--SUBJECTS=-->",subjectList,-1)
     }
     if  onlineAccess != "" {
	     online:="<tr><th>Online access:</th><td>"
	     item:="<div><a href=\""+onlineAccess+"\">Available</a></div>"
	     online=online+item
	     pageString=strings.Replace(pageString,"<!--ONLINE_ACCESS=-->",online,-1)

     }
     if oclcString != "" {
	     worldCat:="<div><h2>"+"<a href=\""+oclcString+"\" target=\"_blank\">"+"This item in Worldcat</a></h2></div>"
	     pageString=strings.Replace(pageString,"<!--WORLDCAT=-->",worldCat,-1)
     }
     staffView:=recordText
     pageString=strings.Replace(pageString,"<!--STAFF_VIEW=-->",staffView,-1)
     if authorityID != "" {
	     oclcIdNetwork:="http://worldcat.org/identities/lccn-"+authorityID
	     idNetwork:="<div><h2>"+"<a href=\""+oclcIdNetwork+"\" target=_blank\">"+"More about this author</a></h2></div>"
	     pageString=strings.Replace(pageString,"<!--OCLC_IDENTITY_NETWORK=-->",idNetwork,-1)
     }
     return  pageString,nil
}


//      didYouMean builds the html page that displays a Did You Mean link.
//      didYouMean receives
//        jsonSlor: the solr description of the spelling suggestion,
//        userQuery: user query,
//        webserverHost: host name of the search platform,
//        cgiPath: CGI path,
//        search_script: CGI script that performs generic search
//        full_page returns the html string and an error object.
//                error == nil, then success
//                error != nil, then failure.
func (page *htmlPage) DidYouMean(jsonSolr [] byte, userQuery string,webserverHost string,cgiPath string,searchScript string) (string,error) {
	   pageString:=page.serverPage
	   l := log.New(os.Stderr, "", 0)
     var jResponse map[string] interface{}
     err1:=json.Unmarshal(jsonSolr,&jResponse)
     if err1 != nil {
          return pageString,errors.New("Invalid json object")
     }
	   header,ok:=jResponse["responseHeader"].(map[string] interface{})
           if !ok   {
//	        printError("Error. couldn't parse json response.")
		return "Error. couldn't parse json response.",errors.New("No Json response")
	   }
	   if header["status"].(float64) != 0 {
  	  	l.Println("status:",header["status"],)
//	        printError("Error. solr invalid request")
		return "Error. solr invalid request",errors.New("solr invalid request.")
	   }
	   jSpellCheck,ok:=jResponse["spellcheck"].(map[string] interface{})
	   if !ok {
 //        printError("FAILED jresponse!")
		return "FAILED jresponse",errors.New("FAILED response")
	   }
	   jCollations,ok:=jSpellCheck["collations"].([]  interface{})
	   if len(jCollations) == 0 {
		noResults:=`<div><h2>No Results Found</h2></div>`
	        pageString=strings.Replace(pageString,"<!--NORESULTS=-->",noResults,-1)
	        inLine,err:=regexp.Compile(`(.*<input type="text".*?value=")(.*?)(.*?)(.*)`)
	        if err != nil {
//	            printError("System error(35)")
		    return  "System error(35)",err
	        }
		pageString=replaceForm(inLine,pageString,userQuery)
		return pageString,nil
	   }
           collation:=jCollations[1].(map[string] interface{})
	   suggested:=collation["collationQuery"].(string)
	   searchURI:=webserverHost+cgiPath+searchScript+"?query="+suggested
           didYouMean:=`<div><span><h2>Did you mean <a href="`+searchURI+`">`+suggested+`</a>?</h2></span></div>`
	   pageString=strings.Replace(pageString,"<!--DIDYOUMEAN=-->",didYouMean,-1)
	   inLine,err:=regexp.Compile(`(.*<input type="text".*?value=")(.*?)(.*?)(.*)`)
	   if err != nil {
//	       l.Println("regexp compile failed",err)
//	       printError("System error(37)")
	       return "System error(37)",err
	   }
	   pageString=replaceForm(inLine,pageString,userQuery)
	return pageString,nil
}

// replaceForm places the user query into the search box of the html file.
// replaceForm receives:
// inPage: the regular expresion that matches the search box,
// pageString: the html page string,
// userQuery: the query string.
// replaceForm returns the  html page as a string.

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

// MultipleRecs builds the html page that displays a list of records 
//  in brief format.
// MultipleRecs receives
//        jsonSolr: the the solr description of records,
//        userQuery: user query,
//        webserverHost: host name of the search platform,
//        cgiPath: CGI path,
//        searchScript: CGI script that performs a solr search,
//        refineResults: the html template for the facet display,
//        facetScript: the script that searches a given facet,
//        facetMarker: place holder for facet display,
//        recordCountMarker: place holder for number of records,
//        fullRecordScript: CGI script that displays a single record,
//        resultsMarker: place holder for record list,
//        pageSize: maximum number of records in a page,
//        previousMarker: place holder for link to previous page,
//        nextMarker: place holder for link to next page,
//  MultipleRecs returns the html string and an error object.
//                error == nil, then success
//                error != nil, then failure.

func (page *htmlPage) MultipleRecs(jsonSolr []byte, userQuery string, webserverHost string, cgiPath string, searchScript string, refineResults string, facetScript string, facetMarker string, recordCountMarker string, fullRecordScript string, resultsMarker string, pageSize string, previousMarker string, nextMarker string) (string, error) {
     pageString:=""
     l:=log.New(os.Stderr, "", 0)
     var jResponse map[string] interface{}
     err1:=json.Unmarshal(jsonSolr,&jResponse)
     if err1 != nil {
          return pageString,errors.New("Invalid json object")
     }
     jresponse,ok:=jResponse["response"].(map[string] interface{})
     if ! ok {
          return pageString,errors.New("Invalid json object")
     }
     numFound:=jresponse["numFound"].(float64)
     startRecord:=jresponse["start"].(float64)

     jdocs,ok:=jresponse["docs"].([] interface{})
     if !ok {
          l.Println("solr didn't return docs")
          return pageString,errors.New("Invalid json object")
     }


	// display multiple results
	refineResultString:=""
        data,err:=ioutil.ReadFile(refineResults)
	if err != nil {
	       l.Println("open failed",err)
	       return "System error(38)",err
        }
        refineResultString=string(data)
	facetInfo,ok:=jResponse["facet_counts"].(map[string] interface{})
	if !ok {
	       l.Println("json response doesn't have facet_counts")
	       return "System error(39)",errors.New("no facet counts in json")
	}
	facetFields,ok:=facetInfo["facet_fields"].(map[string] interface{})
	if !ok {
	       l.Println("facet_counts doesn't have facet_fields")
	       return "System error(40)",errors.New("facet_counts doesn't have facet_fields")
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
	   //l.Println("facet name:",fname)
	   if !ok {
	       l.Println("error retrieving facet names")
	       return "System error(42)",errors.New("error retrieving facet names")
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
	   //l.Println(instance)
           facets[fname]=itemList
	}
//      l.Println(facets)
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
  		       facetQuery:="&q="+quoteUserQuery+"&fq="+key+":"+quoteInstanceValue
//		       facetQuery:="&q="+quoteUserQuery+"&fq="+key+":"+instanceValue
		       facetRequest:=webserverHost+cgiPath+facetScript+"?"+facetQuery
		       // l.Println("facetQuery:",facetRequest)
		       spanE:=`<li><span><a href="`+facetRequest+`">`+instanceValue+`</a>`+`</span>`+`<span>`+" "+instanceCount+`</span>`+"</li>"
		       reqList+=spanE
		   }
            }
	    refineResultString=strings.Replace(refineResultString,htmlMarker,reqList,-1)
	    reqList=""
	}
	resultPage:=""
        resultPage=page.serverPage
	resultPage=strings.Replace(resultPage,facetMarker,refineResultString,-1)
	strNumFound:=strconv.FormatFloat(numFound, 'f', -1, 64)
        resultCount:=`Number of records:`+strNumFound
	resultCount=`<h3>`+resultCount+`</h3>`
	resultPage=strings.Replace(resultPage,recordCountMarker,resultCount,-1)
        recordTable:=""
	recordTable=`<div class="RecResults">`
	recordTable+=`<table class="RecordTable">`
	for _,docs:= range jdocs {
            rec:=docs.(map[string] interface{})
	    recordTxt:=rec["record"].([] interface{})
	    marcText:=recordTxt[0].(string)
	    marc:=biblio.New(marcText)
	    title:=marc.GetTitle()
	    //l.Println("title:",title)
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
//	l.Println("almost there")
	resultPage=strings.Replace(resultPage,resultsMarker,recordTable,-1)
  //   	printPage(resultPage)
        nextPageLink:=""
        previousPageLink:=""
	nextPageElement:=""
	previousPageElement:=""
	startRecordInt:=int64(startRecord)
	pageSizeInt,err2:=strconv.Atoi(pageSize)
	if err2 != nil {
           return "System error(44)",errors.New("Page size conversion failed.")
	}
	numFoundInt:=int64(numFound)
//	if int(start_record) + int(page_size) < int(number_found):
        if startRecordInt + int64(pageSizeInt) <  numFoundInt {
	    nextPageInt:=startRecordInt + int64(pageSizeInt)
	    quotedQuery:=url.QueryEscape(userQuery)
	    nextPageStr:=strconv.FormatInt(nextPageInt,10)
	    nextPageLink=webserverHost+cgiPath+"search?query="+quotedQuery+"&next="+nextPageStr
	    nextPageElement=`<span>  <a href="`+nextPageLink+`" title="Next page"><b>NEXT</b></a>  </span>`
        }
	if startRecordInt - int64(pageSizeInt) >= 0 {
		 nextPageInt:=startRecordInt-int64(pageSizeInt)
	         nextPageStr:=strconv.FormatInt(nextPageInt,10)
	         quotedQuery:=url.QueryEscape(userQuery)
		 previousPageLink=webserverHost+cgiPath+"search?query="+quotedQuery+"&next="+nextPageStr
		 previousPageElement=`<span>  <a href="`+previousPageLink+`" title="Previous page"><b>PREVIOUS</b></a>  </span>`
        }
	resultPage=strings.Replace(resultPage,previousMarker,previousPageElement,-1)
	resultPage=strings.Replace(resultPage,nextMarker,nextPageElement,-1)
	inLine,err:=regexp.Compile(`(.*<input type="text".*?value=")(.*?)(.*?)(.*)`)
	if err != nil {
	         l.Println("regexp compile failed",err)
  	         return "System error(35)",errors.New("regexp compiled failed.")
	}
        resultPage=replaceForm(inLine,resultPage,userQuery)
        return resultPage,nil


     return pageString,nil
}
