#!/usr/bin/env python
from xml.dom import minidom
import urllib
import time
import re
import sys

FORMAT = "[%(levelname)s] %(name)s (%(funcName)s, l%(lineno)d) : %(message)s"

routes = {}
routes["CERN"] = ["56", 1, 0]
routes["HOME"] = ["3", 1, 5]
class TPG(object):
    def __init__(self):
        self.lines = []

    def getLines(self):
        if len(self.lines) == 0:
            data = urllib.urlopen("http://www.tpg.ch/fr/index.php").read()
            r = re.compile('<select id="lineSelector" name="lineSelector" >.*?</select>', re.DOTALL)
            m = r.search(data)
            data = data[m.start():m.end()]
            self.lines = self._parse_xml(data)
        return self.lines

    def _line_id(self, line):
        for i, l in self.getLines():
            if l == line:
                return int(i)
        raise NameError("Line %s not found" % line)

    def getDirs(self, line):
        data = self._fetch_xml(line)
        return self._parse_xml(data)

    def getStops(self, line, direct):
        data = self._fetch_xml(line, direct)
        return self._parse_xml(data)

    def getTimes(self, line, direct, stop):
        data = self._fetch_xml(line, direct, stop)
        return [t for t in self._parse_xml(data,"div","nextDepartureItem") if t is not None]

    def _fetch_xml(self, line=None, direct=None, stop=None):
        url = "http://www.tpg.ch/_services/nextHoraireForm.php?todo=ajaxSearch"
        if line is not None:
            url += "&lineSelector=%d" % self._line_id(line)
        if direct is not None:
            url += "&directionSelector=%s" % direct
        if stop is not None:
            url += "&arretSelector=%s" % stop
        data = urllib.urlopen(url + "&t=%s" % time.strftime("%H:%M:%S")).read()
        return data

    def _parse_xml(self, data, tag_name = "option", tag_class = None):
        dom = minidom.parseString('<?xml version="1.0" encoding="UTF-8"?><tpg>%s</tpg>' % data )
        results = []
        for x in dom.getElementsByTagName(tag_name):
            if x.hasAttribute("value"):
                key = x.getAttribute("value").strip()
            else: key = None
            if tag_class is not None and x.getAttribute("class") != tag_class: continue
            if key is not None and len(key) > 0:
                results.append((key, x.firstChild.nodeValue))
            elif key is None:
                results.append(x.firstChild.nodeValue)
        return results

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

def options(prompt, rows, use_key=False, ncols = 5):
    for i, r in enumerate(rows):
        if i % ncols == 0 and i < len(rows) and i>0:
            print
        if use_key: key = r[1]
        else: key = i
        print ("[%s]" % key).ljust(4) ,
        print r[1].ljust(50/ncols),
    print
    c = raw_input(prompt).strip()
    if use_key:
        for a, b in enumerate(rows):
            if c == b[1]:
                return (b[0], b[1])
    else:
        for a,b in enumerate(rows):
            if int(c) == a:
                return (b[0], b[1], a)
    raise NameError("Invalid choice")

if __name__=="__main__":
    tpg = TPG()
    if len(sys.argv) > 1:
        r = routes[sys.argv[1]]
        title = sys.argv[1]
        line = r[0]
        dirs = tpg.getDirs(line)
        dir_idx = r[1]
        direct = dirs[dir_idx][0]
        stops = tpg.getStops(line, direct)
        stop_idx = r[2]
        stop = stops[stop_idx][0]
    else:
        line = options("Line:", tpg.getLines(), use_key=True)[1]
        dirs = tpg.getDirs(line)
        (direct, n, dir_idx) = options("Direction:", dirs, ncols = 1)
        stops = tpg.getStops(line, direct)
        (stop, n, stop_idx) = options("Stop:", stops, ncols=2)
        title = "Selected"
    print bcolors.HEADER,
    print "%s : Line %s  [%s] @ %s" % (title, line,
                                        dirs[dir_idx][1], stops[stop_idx][1]),
    print bcolors.ENDC
    for  idx, t in enumerate(tpg.getTimes(line, direct, stop)):
        (thours, tmins) = (int(t.split(":")[0]), int(t.split(":")[1]))
        (hours, mins) = (time.localtime().tm_hour, time.localtime().tm_min)
        hdiff = thours - hours
        if thours < hours:
            hdiff = 24 - hours + thours
        mdiff = tmins - mins
        if mdiff < 0:
            hdiff -= 1
            mdiff = (mdiff+60) % 60
        timetogo = hdiff*60 + mdiff
        if timetogo < 5 or timetogo > 120:
            print bcolors.FAIL,
        print "%d: %s (in %d hours %d minutes)" % (idx, t, hdiff, mdiff),
        print bcolors.ENDC
