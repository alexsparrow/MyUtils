#!/usr/bin/env python

# This code implements takes HSBC statements in HTML format
# downloaded from hsbc.co.uk and dumps them into a JSON file.
import re, sys
from xml.dom import minidom
import xml.parsers.expat, time, json, datetime
from optparse import OptionParser

state_date_regex =r'Statement date:.+?<div class="hsbcTextRight">(.*?)</div>'
account_no_regex = """<div class="hsbcAccountNumber">(.*?)</div>"""

class Transaction(object):
     pass

def extract_from_html(path):
     f = open(path, "r")
     data = f.read()
     out = open("tmp.txt", "w+")
     reg = re.compile('<table summary="This table contains a statement of your account">.* \
<tbody>(.*?)</tbody>.*</table>', re.DOTALL)
     data = reg.search(data).group(0)
     data = re.sub("&nbsp;", "", data)
     data = re.sub("&#[0-9].*","",data)
     reg = re.compile(r'href=[\'"]?([^\'" >]+)', re.DOTALL)
     data = reg.sub(r'href="none', data)
     data = re.sub("<strong>(.+?)</strong>",r"\1", data)
     out.write(data)
     try:
          dom = minidom.parseString('<?xml version="1.0" encoding="UTF-8"?><tpg>%s</tpg>' % data)
     except xml.parsers.expat.ExpatError,e:
          print e
          print data.split("\n")[e.lineno-1:e.lineno+1]
          print e.offset
     rows = []
     for tr in dom.getElementsByTagName("tr"):
         row = []
         for td in tr.getElementsByTagName("td"):
             p = td.getElementsByTagName("p")
             if p.length > 0:
                  a = p.item(0).getElementsByTagName("a")
                  if a.length > 0:
                       if a.item(0).firstChild is not None:
                            row.append(a.item(0).firstChild.nodeValue.strip())
                       else: row.append("")
                  elif p.item(0).firstChild is not None:
                       row.append(p.item(0).firstChild.nodeValue.strip())
                  else:
                       row.append("")
             else:
                  row.append("")
         if len(row) > 0:
             rows.append(row)
     return rows

def extract_extra(path):
     info = {}
     reg = re.compile(state_date_regex, re.DOTALL)
     data = open(path,"r").read()
     info["date"] = reg.search(data).group(1)
     reg = re.compile(account_no_regex, re.DOTALL)
     info["account_no"] = reg.search(data).group(1).strip()
     return info

if __name__ == "__main__":
     parser = OptionParser()
     parser.add_option("-y", "--year", help = "Year of Statement",
                       action = "store", type = "int", default=time.localtime().tm_year)
     parser.add_option("-o", "--output", action = "store", type = "string", default = "accounts.json")
     parser.add_option("-a", "--append", action = "store_true", default = False)
     (options, args) = parser.parse_args()
     if options.append: write_mode = "a"
     else: write_mode = "w+"
     fo = open(options.output, write_mode)
     ts = []
     for f in args:
          rows = extract_from_html(f)
          info = extract_extra(f)
          year = info["date"].split()[2]
          for r in rows:
               t = {}
               t["account"] = info["account_no"]
               t["date"] = "%s %s" % (r[0],year) #, "%d %b %Y").str
               if r[1] != "":
                    t["type"] = r[1]
               else: t["type"] = "BAL"

               if r[2] != "":
                    t["description"] = r[2]
               else: t["description"] = ""
               if r[3] != "":
                    t["out"] = float(r[3])
               else:
                    t["out"] = 0.0
               if r[4] != "":
                    t["in"] = float(r[4])
               else:
                    t["in"] = 0.0
               if r[5] != "":
                    t["balance"] = float(r[5])
               else:
                    t["balance"] = -1
               if len(r)>5 and r[5] == "D":
                    t["debt"] = True
               else: t["debt"] = False
               t["statement"] = info["date"]
               ts.append(t)
     fo.write(json.dumps(ts,sort_keys=True, indent=4))
