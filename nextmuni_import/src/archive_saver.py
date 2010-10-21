"""
Takes archived set of nextbus .xml files and dumps them to the DB.
"""

from route_scraper import parse_xml,db

def save_data(xmlfile):
  f = open(xmlfile,'r')
  lines = "\n".join(f.readlines())
  f.close()
  time_retrieved = xmlfile[:xmlfile.find(".")]
  vals = parse_xml(None,lines,time_retrieved=time_retrieved)
  db.update_routes(vals)
  db.commit()
  

