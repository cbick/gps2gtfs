#!/Library/Frameworks/Python.framework/Versions/Current/bin/python

# Copyright (c) 2010 Colin Bick, Robert Damphousse
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

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


def parse_xml(routes,xmldata,time_retrieved=None):
  """time_retrieved should be in seconds since epoch"""
  # parse xml for the route
  doc = xml.parseString(xmldata);

  if time_retrieved is None:
    retrieve_time = dt.datetime.fromtimestamp( 
      int(doc.getElementsByTagName('retrieveTime')[0].getAttribute("time"))
      )
  else:
    fstr = '%Y-%m-%dT%H-%M-%S'
    dstr = time_retrieved[:-5]
    retrieve_time = dt.datetime.strptime(dstr,fstr)
    # time.strftime(fstr,time.gmtime())
    # > '2010-10-19T22-38-47+0000'
    # tar -ztf *.tar.gz
    # > '2010-09-01T23-50-01-0700.tar.gz'
    # retrieve_time = dt.datetime.fromtimestamp(int(time_retrieved))
  print "Retrieve time:",retrieve_time.ctime()

  attributes = [ 'id', 'routeTag', 'dirTag', 'lat', 'lon', 'secsSinceReport', 
                 'predictable', 'heading' ];
  updated_data = [];
  # Save the tracking data
  vehicles = doc.getElementsByTagName('vehicle');
  for vehicle in vehicles:
    vehdata = {'update_time':retrieve_time}
    for attr in attributes:
      vehdata[attr] = vehicle.getAttribute(attr);
    if (not routes) or (vehdata['routeTag'] in routes):
      updated_data.append(vehdata);

  return updated_data;

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
