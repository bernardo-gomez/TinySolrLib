package main
import "fmt"
import "log"
import "strings"
import "os"
import "bufio"
import "net/http"
import "regexp"
import "time"
import "io/ioutil"
import "net/http/cgi"
import "encoding/json"
import "tinylib/displaypage"

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

func  processReq(solrHost string,solrPath string,displayFullRecord string,webserverHost string,cgiPath string,fullRecordScript string,searchScript string,mmsID string,authorizedUser string,authorizedPasswd string) {
	l:=log.New(os.Stderr, "", 0)
        client := &http.Client{
        Timeout: time.Second * 10,
//              Timeout: time.Millisecond * 1,
        }
	reqUrl:=solrHost+solrPath+"select?q=id:"+mmsID
        method:="GET"
// l.Println("url:",reqUrl)
        req, err := http.NewRequest(method, reqUrl, nil)
        if err != nil {
                fmt.Printf("error type: %T\n", err)
                fmt.Printf("error value: %v\n", err)
                log.Fatal("Error reading response. ", err)
                printError("System error(26). NewRequest() failed.")
        }
        req.Header.Set("Cache-Control", "no-cache")
        req.Header.Set("Content-Type", "application/json")
//        user:="tinylib"
//        passwd:="euclid2020"
//        req.SetBasicAuth(user, passwd)
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
	//l.Println("===>",jbody)
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
	_=numFound
	jdocs,ok:=jresponse["docs"].([] interface{})
	if !ok {
   	     l.Println("solr didn't return docs")
  	     printError("FAILED docs!")
   	     return
	}
	recordCount:=len(jdocs)
	fullRecordStr:=""
	data,err:=ioutil.ReadFile(displayFullRecord)
	if err != nil {
	       l.Println("open failed",err)
  	       printError("System error(38)")
	       return
        }
        fullRecordStr=string(data)
	_=fullRecordStr
	_=recordCount
	if recordCount == 1 {
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
        printError("Under construction.")
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
     var fullRecordScript=""
     var displayFullRecord=""
     var formFile=""
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
      if result[1] == "full_record_script" {
          fullRecordScript=result[2]
      }
      if result[1] == "display_full_record" {
          displayFullRecord=result[2]
      }
      if result[1] == "form_file" {
          formFile=result[2]
      }
      if result[1] == "credentials" {
          credentials=result[2]
      }

//      l.Println("regexp :",result[1],result[2])
   }
   if solrHost == "" {
         failed+=1
         l.Println("config param solr_host undefined")
         // printError("System error(6)")
         // os.Exit(0)
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
   if fullRecordScript  == "" {
         failed+=1
         l.Println("config param full_record_script undefined")
   }
   if displayFullRecord  == "" {
         failed+=1
         l.Println("config param display_full_record undefined")
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
   mmsID:=req.Form.Get("id")
   if mmsID == "" {
	 printForm(formFile)
	 os.Exit(0)
   }
   subs,err:=regexp.Compile(`<|>|;|'|&`)
   mmsID=subs.ReplaceAllString(mmsID,"")
   authorization:=strings.Split(credentials,"_|_")
   authorizedUser:=authorization[0]
   authorizedPasswd:=authorization[1]
   processReq(solrHost,solrPath,displayFullRecord,webserverHost,cgiPath,fullRecordScript,searchScript,mmsID,authorizedUser,authorizedPasswd)

}
