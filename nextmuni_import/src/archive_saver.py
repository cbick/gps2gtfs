"""
Takes archived set of nextbus .xml files and dumps them to the DB.
"""

from route_scraper import parse_xml,db
from os import path

def save_data(xmlfile):
  f = open(xmlfile,'r')
  lines = "\n".join(f.readlines())
  f.close()
  xmlfile = path.basename(xmlfile)
  time_retrieved = xmlfile[:xmlfile.find(".")]
  vals = parse_xml(None,lines,time_retrieved=time_retrieved)
  db.update_routes(vals)
  db.commit()
  

if __name__=="__main__":
  import sys
  if len(sys.argv) != 2:
    print "Usage: %s fname" % (sys.argv[0],)
    sys.exit(1)
  save_data(sys.argv[1])

