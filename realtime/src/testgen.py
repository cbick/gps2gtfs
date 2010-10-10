# creates xml files based on schedule

import dbqueries as db
from random import random
import GTFSBusTrack as gtfs
import xml.dom.minidom as xml
import datetime as dt
import time

def choose_random_trip(date):
  sids = db.get_serviceIDs_for_date(date);

  randomsid = sids[ int( random()*len(sids) ) ]

  cur = db.get_cursor()
  db.SQLExec(cur, """
select trip_id from gtf_trips where service_id=%(sid)s order by random() limit 1
""",
             {'sid':randomsid})
  ret = cur.fetchall()
  cur.close()
  return ret[0][0]

def choose_random_date():
  # for now just returns Oct1, sorry
  return dt.date( 2010, 10, 1 )


def get_filename(date,time_secs):
  # date is dt.date
  # time_secs is seconds into day
  ret = str( int(time.mktime(time.strptime(date.ctime()))) 
             + time_secs )
  return ret

def make_dirtag(sched):
  ret = sched.route_short_name + "__"
  if sched.direction_id == 0:
    ret += "OB"
  else:
    ret += "IB"
  return ret

def make_xml(sched,date):
  stops = sched.stops
  vehicle_id = "randomvid_%d" % (int(random() * 10000))
  # add fake stop at the end to trigger route match
  stops.append( None )
  for stop in stops:
    #<vehicle id="1050" routeTag="F" dirTag="F__IBCTRO" 
    #lat="37.77719" lon="-122.41677" secsSinceReport="19" 
    #predictable="true" heading="44" speedKmHr="25.992"/>
    doc = xml.getDOMImplementation().createDocument(None,"body",None)
    top = doc.documentElement
    velt = doc.createElement("vehicle")
    attrs = { 'id' : vehicle_id,
              'routeTag' : sched.route_short_name,
              'dirTag' : make_dirtag(sched),
              'secsSinceReport' : "0",
              'predictable' : 'true',
              'heading' : "0",
              'speedKmHr' : "25"
              }
    if stop is not None:
      attrs['lat'] = str(stop['stop_lat'])
      attrs['lon'] = str(stop['stop_lon'])
      fname = get_filename(date,stop['arrival_time_seconds'])
    else:
      attrs['dirTag'] = 'null'
      attrs['routeTag'] = 'null'
      attrs['lat'] = str(0)
      attrs['lon'] = str(0)
      fname = str( int(fname) + 1 )

    for attr,val in attrs.items():
      velt.setAttribute(attr,val)
    
    telt = doc.createElement("retrieveTime")
    telt.setAttribute("time",fname)

    top.appendChild(velt)
    top.appendChild(telt)

    f = open(fname+'.xml','w')
    f.write( doc.toxml() )
    f.close()
  


def run():
  date = choose_random_date()
  print "Chose random date",date
  trip_id = choose_random_trip(date)
  print "Chose random trip",trip_id
  sched = gtfs.GTFSBusSchedule(trip_id)
  
  xml = make_xml(sched,date)
  
if __name__ == "__main__":
  run()

