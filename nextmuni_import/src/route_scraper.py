import urllib as url
import xml.dom.minidom as xml
import time
import datetime as dt

from os import path,sys  
mydir = path.abspath(path.dirname(sys.argv[0]))
coredir = mydir + "/../../core/src/"
sys.path.append(coredir)
import dbqueries as db


def read_routes(fname):
  f = open(fname,'r');
  lines = f.readlines();
  f.close();
  lines = filter(lambda line: line and not line.startswith("#"),
                 map(str.strip,lines));
  return lines;

def get_updated_routes(routes):
  format_URL = "http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=sf-muni&t=0"

  attributes = [ 'id', 'routeTag', 'dirTag', 'lat', 'lon', 'secsSinceReport', 
                 'predictable', 'heading' ];
  updated_data = [];

  # Retrieve/parse xml for the route
  retrieve_time = dt.datetime.now();
  resp = url.urlopen(format_URL);
  respdata = "".join(resp.readlines());
  resp.close();
  doc = xml.parseString(respdata);

  # Save the tracking data
  vehicles = doc.getElementsByTagName('vehicle');
  for vehicle in vehicles:
    vehdata = {'update_time':retrieve_time}
    for attr in attributes:
      vehdata[attr] = vehicle.getAttribute(attr);
    if (not routes) or (vehdata['routeTag'] in routes):
      updated_data.append(vehdata);

  return updated_data;


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print
    print "Usage: %s filename" % sys.argv
    print "  The file should have a line-by-line listing of route ID's."
    print "  You may comment out lines with a #"
    print
    print "  *** To retrieve ALL route ID's, try '%s ALL'." % sys.argv
    print
    sys.exit(1)

  print "Retrieving data on",time.ctime(),"..."
  sys.stdout.flush()
  fname = sys.argv[1]
  if fname=="ALL":
    routes = None
  else:
    routes = read_routes(fname);
  updated_routes = get_updated_routes(routes);
  db.update_routes(updated_routes);
  db.commit();
  print "... Done (",time.ctime(),").\n"
  sys.stdout.flush()
