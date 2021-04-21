//package biblio creates MARC fields as text strings
package biblio

import (
//       "fmt"
       "strings"
        "regexp"
//	"log"
)

type record  struct { 
    text []  string
}

func New(marc string) record {
    var rec record
    rec.text=strings.Split(marc,"\n")
//    fmt.Fprintf(os.Stderr,marc)
    return rec
}

func (rec *record) GetLeader() string {
    leader:=""
    for _,field := range rec.text {
          if len(field) < 4 {
		  continue
	  }
        if field[0:4] == "=LDR"{
           leader=field[6:]
           break
        }
    }
    return  leader
}

func (rec *record) GetResourceType() string {
    leader:=""
    for _,field := range rec.text {
        if len(field) < 4 {
	    continue
	}
        if field[0:4] == "=LDR"{
           leader=field[6:]
           break
        }
    }
    if leader == "" {
       return ""
    }
    rTypeMap:= map[string] string {"aa":"Book","ac":"Book",
        "ad":"Book","am":"Book",
       "ta":"Book", "tc":"Book","td":"Book", "tm":"Book",
        "ab":"Periodical","ai":"Periodical",
        "as":"Periodical",
        "ca":"Score", "cb":"Score","cc":"Score",
        "cd":"Score", "ci":"Score","cm":"Score",
        "ea":"Map","eb":"Map","ec":"Map","ed":"Map","ei":"Map",
        "em":"Map","es":"Map",
        "im":"Sound recording","it": "Sound recording",
        "ja":"Sound recording","jb":"Sound recording","jc":"Sound recording",
        "jd":"Sound recording","ji":"Sound recording","jm":"Sound recording",
        "js":"Sound recording",
        "ga":"Video", "gb":"Video", "gc":"Video", "gd":"Video",
        "gi":"Video", "gm":"Video", "gs":"Video",
        "pc":"Archive", "pa":"Archive", "pm":"Archive",
        "ma":"Computer file","mb":"Computer file","mc":"Computer file",
        "md":"Computer file","mi":"Computer file","mm":"Computer file",
        "ms":"Computer file",
        }
    leader0607:=leader[6:8]
    rType,ok:=rTypeMap[leader0607]
    if ok == false {
        rType=""
    }
    return  rType
}


func (rec *record) GetISBN() string {
   digits,err:=regexp.Compile(`(\d+)`)
   if err != nil {
        return ""
   }
   isbn:=""
   for _,field := range rec.text {
       if len(field) < 4 {
 	  continue
       }
       if field[0:4] == "=020" {
           txt:=field[8:]
           subfield:=strings.Split(txt,"$")
           //fmt.Println(subfield)
           for _,subf := range subfield{
             if subf != "" {
                 if subf[0:1] == "a"{
                    //fmt.Println(subf[1:])
                    result:=digits.FindStringSubmatch(subf[1:])
                    if len(result) > 0 {
                        // fmt.Println(result)
                        isbn=result[1]
                        return isbn
                    }
                 }
             }
           }
       }
   }
   return isbn
}


func (rec *record) GetRecordID() string {
   digits,err:=regexp.Compile(`(\d+)`)
   if err != nil {
        return ""
   }
   recid:=""
   for _,field := range rec.text {
       if len(field) < 4 {
           continue
       }
       if field[0:4] == "=001" {
           txt:=field[6:]
           result:=digits.FindStringSubmatch(txt)
           if len(result) > 0{
                  recid=result[1]
                  return recid
           }
       }
   }
   return recid
}

// def get_language(self):
//    """
//     it retrieves the language based on the
//    MARC 008.
// """
//language=""
//    for field in self.marc:
//        if field[0:4] == "=008":
//             language=field[41:44]
//             return str(language)
//    return language


func (rec *record) GetLanguage() string {
     language:=""
     for _,field := range rec.text {
        if len(field) < 4 {
	   continue
	}
        if field[0:4] == "=008" {
            language=field[41:44]
	    break
	}
     }
     return language
}
func (rec *record) GetOclcString() string {
      oclcString:=""
      oclc1,err:=regexp.Compile(`o(\d+)`)
      if err != nil {
	  return ""
      }
      oclc2,err:=regexp.Compile(`ocm(\d+)`)
      if err != nil {
	  return ""
      }
      oclc3,err:=regexp.Compile(`ocn(\d+)`)
      if err != nil {
	  return ""
      }
      oclc4,err:=regexp.Compile(`\(OCoLC\)(\d+)`)
      if err != nil {
	  return ""
      }
      oclcNumber:=""
      found:=false
      for _,field := range rec.text {
        if len(field) < 4 {
	    continue
	}
        if field[0:4] == "=035" {
            txt:=field[8:]
            subfield:=strings.Split(txt,"$")
            for _,subf := range subfield{
               if subf != "" {
                  if subf[0:1] == "a"{
                      result:=oclc1.FindStringSubmatch(subf[1:])
		      if  len(result) > 0 {
			  oclcNumber=result[1]
			  found=true
			  break
		      }
                      result=oclc2.FindStringSubmatch(subf[1:])
		      if  len(result) > 0 {
			  oclcNumber=result[1]
			  found=true
			  break
		      }
                      result=oclc3.FindStringSubmatch(subf[1:])
		      if  len(result) > 0 {
			  oclcNumber=result[1]
			  found=true
			  break
		      }
                      result=oclc4.FindStringSubmatch(subf[1:])
		      if  len(result) > 0 {
			  oclcNumber=result[1]
			  found=true
			  break
		      }
                  }
               }
	    }
        }
     }
     if found {
            oclcString="https://www.worldcat.org/oclc/"+oclcNumber
     }
      return  oclcString
}

func (rec *record) GetTitle() string {
	title:=""
	title880:=""
	// l := log.New(os.Stderr, "", 0)
        subfa:=""
        subfb:=""
        subfa880:=""
        subfb880:=""
	var titleIs880 bool
	titleIs880=false
        for _,field := range rec.text {
          if len(field) < 4 {
	      continue
	  }
          if field[0:4] == "=245" {
              txt:=field[8:]
              subfield:=strings.Split(txt,"$")
              for _,subf := range subfield{
                 if subf != "" {
                    if subf[0:1] == "a"{
			subfa=subf[1:]
	            } else if subf[0:1] == "b" {
			subfb=subf[1:]
	            }
		 }
	      }
              title=subfa+" "+subfb
              title=strings.Replace(title,"/","",-1)
	  }
	  if field[0:4] == "=880" &&  !titleIs880 {
               text:=field[8:]
	       subfield:=strings.Split(text,"$")
               for _,subf:=  range  subfield {
                  if subf != "" {
                    if subf[0:1] == "6" {
                        if subf[1:4] == "245"{
                            titleIs880=true
                        }
                    } else if subf[0:1] == "a" {
                        subfa880=subf[1:]
                    } else if subf[0:1] == "b" {
                        subfb880=subf[1:]
                    }
                  }
               }
               if titleIs880 {
                   title880=subfa880+" "+subfb880
                   title880=strings.Replace(title880,"/","",-1)
               }
          }
        }
	if  title880 != "" {
	      title=title880
        }
	return title
}

func (rec *record) GetAuthor() [] string {
	var nameList [] string
	var nameList880 [] string
	name:=""
	name880:=""
	nameIs880:=false
	ignoreIt:=false
        for _,field := range rec.text {
	    if len(field) < 5 {
		  continue
            }
            if field[0:4] == "=100" {
	       ignoreIt=false
               txt:=field[8:]
               subfield:=strings.Split(txt,"$")
               for _,subf := range subfield {
                  if subf != "" {
                     if subf[0:1] == "6"{
			     ignoreIt=true
		     }
                     if subf[0:1] == "a"{
			 name=subf[1:]
			 name=strings.Replace(name,",","",-1)
			 name=strings.Replace(name,".","",-1)
			 name=strings.Replace(name,"/","",-1)
	             }
	          }
	       }
	       if !ignoreIt {
		    nameList=append(nameList,name)
	       }
            }  else if  field[0:4] == "=700" {
	          ignoreIt=false
                  txt:=field[8:]
                  subfield:=strings.Split(txt,"$")
                  for _,subf := range subfield {
                     if subf != "" {
                        if subf[0:1] == "6"{
			     ignoreIt=true
		        }
                        if subf[0:1] == "a"{
		  	       name=subf[1:]
			       name=strings.Replace(name,",","",-1)
			       name=strings.Replace(name,".","",-1)
			       name=strings.Replace(name,"/","",-1)
		        }
	             }
	          }
	          if !ignoreIt {
		      nameList=append(nameList,name)
	          }
            } else if field[0:4] == "=880" {
                  txt:=field[8:]
                  subfield:=strings.Split(txt,"$")
		  name880=""
                  for _,subf := range subfield {
                     if subf != "" {
			   if subf[0:1] == "6" {
				if subf[1:4] == "700" {
				    nameIs880=true
				}
				if subf[1:4] == "100" {
				    nameIs880=true
				}
			} else if subf[0:1] == "a" {
				name880=subf[1:]
				name880=strings.Replace(name880,"\u060c","",-1)
				name880=strings.Replace(name880,".","",-1)
				name880=strings.Replace(name880,"/","",-1)
				name880=strings.Replace(name880,",","",-1)
			}
		     }
		  }
		  if nameIs880 {
		     nameList880=append(nameList880,name880)
	          }
            }
	}
	nameList=append(nameList,nameList880...)
        return nameList
}


func (rec *record) GetCreator() string {
       name:=""
       name880:=""
       nameIs880:=false
       for _,field := range rec.text {
	    if len(field) < 5 {
		  continue
            }
           if field[0:4] == "=100" {
              txt:=field[8:]
              subfield:=strings.Split(txt,"$")
              for _,subf := range subfield{
                    if subf != "" {
                        if subf[0:1] == "a"{
			    if subf[len(subf)-1] == ',' {
                               name=subf[1:len(subf)-1]+"."
		            } else {
				   name=subf[1:]
		            }
			    name=strings.Replace(name,"..",".",-1)
		        }
	            }
	      }
	  } //
          if field[0:4] == "=880" && !nameIs880 {
		  text:=field[8:]
		  subfield:=strings.Split(text,"$")
		  for _,subf:= range  subfield {
			 if subf !=  ""{
			    if subf[0:1] == "6"{
				  if subf[1:4] == "100"{
				     nameIs880=true
				  }
			    } else if subf[0:1] == "a"{
				   name880=subf[1:]
			    }
			 }
		  }
		  if nameIs880 {
			name880=strings.Replace(name880,"..",".",-1)
	          }
          }
       }
       if nameIs880 {
	    name=name880
       }
       return name
}

func (rec *record) GetContributor() [] string {
	var nameList [] string
	var nameList880  [] string
	nameIs880:=false
	name:=""
	name880:=""
        for _,field := range rec.text {
	    if len(field) < 5 {
		  continue
            }
            if field[0:4] == "=700" {
               txt:=field[8:]
	       ignoreIt:=false
               subfield:=strings.Split(txt,"$")
               for _,subf := range subfield {
                  if subf != "" {
		     if subf[0:1] == "6" {
			     ignoreIt=true
		     }
                     if subf[0:1] == "a"{
			 if subf[len(subf)-1] == ',' {
				name=subf[1:len(subf)-1]+"."
			 } else {
				 name=subf[1:]
			 }
	             }
	          }
	       } //
	       if ! ignoreIt {
		       name=strings.Replace(name,"..",".",-1)
		       nameList=append(nameList,name)
	       }
            }
            if field[0:4] == "=880" {
		   nameIs880=false 
                   txt:=field[8:]
		   name880=""
                   subfield:=strings.Split(txt,"$")
                   for _,subf := range subfield {
			   if subf != "" {
			       if subf[0:1] == "6"{
				       if subf[1:4] == "700"{
					    nameIs880=true
				       }
			       } else if subf[0:1] == "a"{
				       name880=subf[1:]
			       }
			   }
		   } //
		   if name880 != "" && nameIs880 {
			  nameList880=append(nameList880,name880)
		   }
	    }
        }
	if len(nameList880) > 0{
		 nameList=append(nameList,nameList880...)
	}
	return nameList
}

func (rec *record) GetPublicationInfo() string {
	publicationInfo:=""
	subfa:=""
	subfb:=""
	subfc:=""
        for _,field := range rec.text {
	    if len(field) < 5 {
		  continue
            }
	    if field[0:4] == "=264" && field[7:8] == "1"{
		 txt:=field[8:]
		 subfield:=strings.Split(txt,"$")
                 for _,subf := range subfield {
	            if subf != "" {
                       if subf[0:1] == "a" {
			   subfa=subf[1:]
			   subfa=strings.Replace(subfa,"[","",-1)
			   subfa=strings.Replace(subfa,"]","",-1)
		       } else if subf[0:1] == "b" {
			   subfb=subf[1:]
	               } else if subf[0:1] == "c" {
			   subfc=subf[1:]
			   subfc=strings.Replace(subfc,"[","",-1)
			   subfc=strings.Replace(subfc,"]","",-1)
	               }
		    }
	         }
	         publicationInfo=subfa+" "+subfb+" "+subfc
            }
	    if  publicationInfo == "" {
	        if field[0:4] == "=260" {
		    txt:=field[8:]
		    subfield:=strings.Split(txt,"$")
                    for _,subf := range subfield {
	               if subf != "" {
                          if subf[0:1] == "a" {
			      subfa=subf[1:]
			      subfa=strings.Replace(subfa,"[","",-1)
			      subfa=strings.Replace(subfa,"]","",-1)
		          } else if subf[0:1] == "b" {
			      subfb=subf[1:]
	                  } else if subf[0:1] == "c" {
			     subfc=subf[1:]
			     subfc=strings.Replace(subfc,"[","",-1)
			     subfc=strings.Replace(subfc,"]","",-1)
	                  }
		       }
		    }
	            publicationInfo=subfa+" "+subfb+" "+subfc
	        }
            }
	}
	return publicationInfo
}

func (rec *record) GetPublisher() string {
     publisher:=""
     subfa:=""
     subfb:=""
     for _,field := range rec.text {
	    if len(field) < 5 {
		  continue
            }
	    if field[0:4] == "=264" && field[7:8] == "1"{
		 txt:=field[8:]
		 subfield:=strings.Split(txt,"$")
                 for _,subf := range subfield {
	            if subf != "" {
                       if subf[0:1] == "a" {
			   subfa=subf[1:]
			   subfa=strings.Replace(subfa,"[","",-1)
			   subfa=strings.Replace(subfa,"]","",-1)
		       } else if subf[0:1] == "b" {
			   subfb=subf[1:]
			   subfb=strings.Replace(subfb,",","",-1)
	               }
		    }
	         }
	         publisher=subfa+" "+subfb
            }
	    if  publisher == "" {
	        if field[0:4] == "=260" {
		    txt:=field[8:]
		    subfield:=strings.Split(txt,"$")
                    for _,subf := range subfield {
	               if subf != "" {
                          if subf[0:1] == "a" {
			      subfa=subf[1:]
			      subfa=strings.Replace(subfa,"[","",-1)
			      subfa=strings.Replace(subfa,"]","",-1)
		          } else if subf[0:1] == "b" {
			      subfb=subf[1:]
			      subfb=strings.Replace(subfb,",","",-1)
	                  } 
		       }
		    }
	            publisher=subfa+" "+subfb
	        }
            }
	}
	return publisher
}


func (rec *record) GetPublicationDate() string {
     pubDate:=""
     subfc:=""
     for _,field := range rec.text {
	    if len(field) < 5 {
		  continue
            }
	    if field[0:4] == "=264" && field[7:8] == "1"{
		 txt:=field[8:]
		 subfield:=strings.Split(txt,"$")
                 for _,subf := range subfield {
	            if subf != "" {
                       if subf[0:1] == "c" {
			   subfc=subf[1:]
			   subfc=strings.Replace(subfc,"[","",-1)
			   subfc=strings.Replace(subfc,"]","",-1)
		       }
		    }
	         }
	         pubDate=subfc
            }
	    if  pubDate == "" {
	        if field[0:4] == "=260" {
		    txt:=field[8:]
		    subfield:=strings.Split(txt,"$")
                    for _,subf := range subfield {
	               if subf != "" {
                          if subf[0:1] == "c" {
			      subfc=subf[1:]
			      subfc=strings.Replace(subfc,"[","",-1)
			      subfc=strings.Replace(subfc,"]","",-1)
		          } 
		       }
		    }
	            pubDate=subfc
	        }
            }
	}
	return pubDate
}


func (rec *record) GetTopic() [] string {
        var topic [] string
	subfa:=""
        for _,field := range rec.text {
	    if len(field) < 5 {
		  continue
            }
            if field[0:4] == "=650" {
               txt:=field[8:]
               subfield:=strings.Split(txt,"$")
               for _,subf := range subfield {
                  if subf != "" {
                     if subf[0:1] == "a"{
                         subfa=subf[1:]
                         topic=append(topic,subfa)
                     }
                  }
               }
            }
        }
	uniqueTopic:=unique(topic)
        return uniqueTopic
}

// Golang Function that Removes Duplicate
// Elements From the Array
func unique(arr []string ) []string  {
	occured := map[string]bool{}
	var result  []string
	for _,e := range arr {

		// check if already the mapped
		// variable is set to true or not
		if occured[e] != true {
			occured[e] = true
			// Append to result slice.
			result = append(result, e)
		}
	}

	return result
}


func (rec *record) GetGenre() [] string {
        var genre [] string
	subfa:=""
        for _,field := range rec.text {
	    if len(field) < 5 {
		  continue
            }
            if field[0:4] == "=655" {
               txt:=field[8:]
               subfield:=strings.Split(txt,"$")
               for _,subf := range subfield {
                  if subf != "" {
                     if subf[0:1] == "a"{
                         subfa=subf[1:]
                         genre=append(genre,subfa)
                     }
                  }
               }
            }
        }
	uniqueGenre:=unique(genre)
        return uniqueGenre
}


func (rec *record) GetNumberPages() string {
     pagesString:=""
     pages,err:=regexp.Compile(`[^0-9]*([0-9]+) pages.*`)
     if err != nil {
	    return pagesString
     }
     for _,field := range rec.text {
	    if len(field) < 5 {
		  continue
            }
	    if field[0:4] == "=300" {
		 txt:=field[8:]
		 subfield:=strings.Split(txt,"$")
                 for _,subf := range subfield {
	            if subf != "" {
                       if subf[0:1] == "a" {
                           result:=pages.FindStringSubmatch(subf[1:])
			   if  len(result) > 0 {
				   pagesString="Number of Pages: "+result[1]
		           }
		       }
		    }
	         }
            }
     }
     return pagesString
}

//   def get_book_contributor_info(self):
//      """
//         it retrieves book contributor based on the
//         MARC 700 and the contributor's role.
//      """
//      name=""
//      name_string=""
//      contributor_role="contributor"
//      editor_list=[]
//      contributor_list=[]
//      translator_list=[]
//      illustrator_list=[]
//      contributor_list=[]
//      producer_list=[]
//
//      for rec in self.lines:
//         if rec[0:3] == "700":
//           deathdate=""
//           birthdate=""
//           text=rec[7:]
//           #print text
//           contributor_role="contributor"
//           subfield=text.split("$$")
//           contrib_name=""
//           name=""
//           for sf in subfield:
//             if sf != "":
//                if sf[0:1] == "a":
//                   contrib_name=sf[1:]
//                   contrib_name=contrib_name.rstrip(",")
//                elif sf[0:1] == "d":
//                      date=sf[1:]
//                      date=date.rstrip(".")
//                      date_info=date.split("-")
//                      #sys.stderr.write("date:"+str(date_info)+"\n")
//                      if date_info[0] != "":
//                         birthdate=date_info[0]
//                      if date_info[1] != "":
//                         deathdate=date_info[1]
//                elif sf[0:1] == "e":
//                   this_role=sf[1:].lower()
//                   this_role=this_role.replace(".","")
//                   role_word=this_role.split(" ")
//                   if "editor" in role_word:
//                      contributor_role="editor"
//                   elif "translator" in role_word:
//                      contributor_role="translator"
//                   elif "illustrator" in role_word:
//                      contributor_role="illustrator"
//                   elif "producer" in role_word:
//                       contributor_role="producer"
//                   else:
//                       contributor_role="contributor"
//           if contrib_name != "":
//                 name+="{\"name\":\""+contrib_name+"\""
//                 if birthdate != "":
//                      name+=","+"\n"+"  \"birthDate\": \""+birthdate+"\""
//                 if deathdate != "":
//                      name+=","+"\n"+"  \"deathDate\": \""+deathdate+"\""+"\n"
//                 name+="},\n"
//                 if contributor_role == "editor":
//                    editor_list.append(name)
//                    name=""
//                 if contributor_role == "translator":
//                    translator_list.append(name)
//                    name=""
//                 if contributor_role == "producer":
//                    producer_list.append(name)
//                    name=""
//                 if contributor_role == "contributor":
//                    contributor_list.append(name)
//                    name=""
//                 if contributor_role == "illustrator":
//                    illustrator_list.append(name)
//                    name=""
//
//         elif rec[0:3] == "x10":  ### exclude 710 for the time being
//           deathdate=""
//           birthdate=""
//           text=rec[7:]
//           #print text
//           subfield=text.split("$$")
//           contrib_name=""
//           name=""
//           for sf in subfield:
//             if sf != "":
//                if sf[0:1] == "a":
//                   contrib_name=sf[1:]
//                   contrib_name=contrib_name.rstrip(",")
//
//
//           if contrib_name != "":
//                 name+="{\"name\":\""+contrib_name+"\""
//                 if birthdate != "":
//                      name+=","+"\n"+"  \"birthDate\": \""+birthdate+"\""
//                 if deathdate != "":
//                      name+=","+"\n"+"  \"deathDate\": \""+deathdate+"\""+"\n"
//                 name+="},\n"
//                 if contributor_role == "editor":
//                    editor_list.append(name)
//                    name=""
//                 if contributor_role == "translator":
//                    translator_list.append(name)
//                    name=""
//                 if contributor_role == "producer":
//                    producer_list.append(name)
//                    name=""
//                 if contributor_role == "contributor":
//                    contributor_list.append(name)
//                    name=""
//                 if contributor_role == "illustrator":
//                    illustrator_list.append(name)
//                    name=""
//      if len(contributor_list) > 0:
//         name_string+="\"contributor\": ["+"\n"
//         for entry in contributor_list:
//           name_string+=entry
//         name_string=name_string.rstrip("\n")
//         name_string=name_string.rstrip(",")
//         name_string+="\n],"
//      if len(editor_list) > 0:
//         name_string+="\"editor\": ["+"\n"
//         for entry in editor_list:
//           name_string+=entry
//         name_string=name_string.rstrip("\n")
//         name_string=name_string.rstrip(",")
//         name_string+="\n],\n"
//      if len(translator_list) > 0:
//         name_string+="\"translator\": ["+"\n"
//         for entry in translator_list:
//           name_string+=entry
//         name_string=name_string.rstrip("\n")
//         name_string=name_string.rstrip(",")
//         name_string+="\n],"
//      if len(illustrator_list) > 0:
//         name_string+="\"illustrator\": ["+"\n"
//         for entry in illustrator_list:
//           name_string+=entry
//         name_string=name_string.rstrip("\n")
//         name_string=name_string.rstrip(",")
//         name_string+="\n],"
//      if len(producer_list) > 0:
//         name_string+="\"producer\": ["+"\n"
//         for entry in producer_list:
//           name_string+=entry
//         name_string=name_string.rstrip("\n")
//         name_string=name_string.rstrip(",")
//         name_string+="\n],"
//      name_string=name_string.rstrip("\n")
//      name_string=name_string.rstrip(",")
//      return name_string
//


func (rec *record) GetURL() string {
     url:=""
     for _,field := range rec.text {
	    if len(field) < 5 {
		  continue
            }
	    if field[0:4] == "=856" {
		 if field[6:8] == "40" {
		    txt:=field[8:]
		    subfield:=strings.Split(txt,"$")
                    for _,subf := range subfield {
	               if subf != "" {
                          if subf[0:1] == "u" {
				  url:=subf[1:]
				  return url
		          }
		       }
		    }
	         }
            }
    }
    return url
}
