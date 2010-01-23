# Copyright (c) 2010 Colin Bick, Robert Damphousse

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
Here we implement the preprocessing methods necessary to mine the
bus tracking data. The fundamental step is to determine when a bus
arrives at a stop, and when it _should_ have arrived.

Due to the size of the dataset, it's best to select a somewhat
representative subset spanning the available time period. In other
words we'll pick just a few routes of different types and analyze
their data for every day available.

The difficulties inherent with matching GPS data with GTFS data,
deciding when a GPS bus has arrived at a stop, and filtering out
faulty GPS data are all dealt with in the GPSBusTrack code, and
we will make fair use of it here.
"""

import dbqueries as db
import gisutils as gis
import GPSBusTrack as gps
import GPSDataTools as gpstool
import GTFSBusTrack as gtfs




### EARLYBIRDS ###

def fix_all_earlybirds():
  segs = db.get_segment_IDs();
  for i,seg_id in enumerate(segs):
    correct_earlybird(seg_id);
    print "%6.2f%%" % (100*i/float(len(segs)),)


def correct_earlybird( segment_id, early_tolerance=300, late_tolerance=0 ):
  """
  Checks to see if the arrival schedule for segment_id is consistently
  early as specified by early_tolerance, and if so, assigns it to the 
  GTFS trip directly previous to its current assignment.

  early_tolerance defines how early this bus' early mean must be, in
  seconds, for it to be considered an early bird.

  late_tolerance defines the maximum lateness in seconds of the bus 
  after reassignment; if the mean lateness is greater than this amount,
  then the reassignment is not made. Can be None to specify we don't care
  how late we are after reassignment.
  """

  sched = gps.GPSSchedule(segment_id);
  earliness,lateness = sched.getEarlyAndLateMeans();
  if earliness > early_tolerance and lateness <= late_tolerance:
    prev_trips = db.get_previous_trip_ID(sched.trip_id,sched.trip_date,
                                         sched.schedule_offset,
                                         numtrips=20);
      
    for prev_trip_id,new_offset in prev_trips:
      bus_new = gps.GPSBusSchedule(segment_id,prev_trip_id,new_offset);
      bt = bus_new.getGPSBusTrack();
      new_early,new_late = sched.getEarlyAndLateMeans(bus_new.getGPSSchedule());
      print "  ",new_early,new_late
      # break as soon as we find an improvement
      if new_late > late_tolerance:# and new_early < early_tolerance:
        break
      prev_trip_id,new_offset = None,None

    print "Early Segment ID:",segment_id
    print "  Old trip, earliness, lateness:",
    print sched.trip_id,earliness,lateness
    print "Old num stops with arrivals:",sched.getNumTimePoints()
    old_dist, old_oob = bt.measureDistanceFromGTFSTrip(sched.trip_id,
                                                       sched.schedule_offset,
                                                       penalize_gps_oob=True,
                                                       penalize_gtfs_oob=False);

    
    if prev_trip_id is None:
      print "NO REPLACEMENT FOUND"
      return
    
    print "  New trip, earliness, lateness:",
    print prev_trip_id,new_early,new_late
    new_dist,new_oob = bt.measureDistanceFromGTFSTrip(prev_trip_id,
                                                      new_offset,
                                                      penalize_gps_oob=True,
                                                      penalize_gtfs_oob=False);

    print "New num stops with arrivals:",
    print sched.getNumTimePoints(bus_new.getGPSSchedule());
    #if new_oob <= 0.75:
    print "+Corrected."
    db.correct_gps_schedule(segment_id,prev_trip_id,new_dist,new_offset,
                            bus_new.getGPSSchedule());
    #else:
    #  print "-Ignored."






### GPS<->GTFS MATCHUPS ###

def load_and_cache_routes(routes = ['18']):
  for route in routes:
    print "Caching route",route,"..."
    load_and_cache_route(route);
    print "... done caching route."

def load_and_cache_route( route_name ):
  """
  Given a route_short_name, loads all data available for that route 
  from GPS data, matches to GTFS schedule, and exports all valid trips found.
  """

  # Load the data
  rte = gpstool.Route( route_name );
  
  # Export valid segments
  rte.export_segments(True);
    



### GPS SCHEDULES ###

def create_all_actual_timetables():
  for seg_id in db.get_segment_IDs(True):
    create_actual_timetable(seg_id)
  db.commit();

def create_actual_timetable( segment_id ):
  """
  Given a segment id from the cached trips data, finds actual arrival
  times at each of the GTFS scheduled stops and stores in the database.
  """
  # Load the data
  print "Loading segment",segment_id,"...",
  bus = gps.GPSBusSchedule(segment_id);
  print "ok"
  
  # Export the data
  print "Exporting schedule...",
  db.export_gps_schedule(segment_id,bus.getGPSSchedule());
  print "ok"



### TRIPS ###

def populate_all_trip_information():
  trip_ids = db.get_all_trip_ids();
  for i,trip_id in enumerate(trip_ids):
    print "%d/%d" %(i+1,len(trip_ids))
    populate_trip_information(trip_id);

def populate_trip_information(trip_id):
  """
  Given a GTFS trip ID, populates information about that trip into the database.
  """

  trip_info,stops,shape = db.getGTFSTripData(trip_id);
  arrive_times = map(lambda s:s['arrival_time_seconds'],stops);
  depart_times = map(lambda s:s['departure_time_seconds'],stops);
  if len(arrive_times) == 0:
    print "NO SCHEDULE DATA",trip_id
    return
  first_arrive = min(arrive_times);
  first_depart = min(depart_times);
  last_arrive = max(arrive_times);
  if first_depart is not None:
    trip_duration = last_arrive - first_depart
  else:
    trip_duration = last_arrive - first_arrive

  trip_length = populate_trip_stop_information(trip_id,stops);

  db.export_trip_information(trip_id,first_arrive,first_depart,
                          trip_length,trip_duration);


def populate_trip_stop_information(trip_id,stops):
  """
  Given a GTFS trip ID, populates information about each stop in that trip
  into the database.
  Returns total length of the trip in meters.
  """
  cumulative_dist = 0.0
  prev_stop_loc = None  
  
  for i,gstop in enumerate(stops):
    stop_loc=gstop['stop_lat'],gstop['stop_lon']
    stop_arrive=gstop['arrival_time_seconds']
    stop_depart = gstop['departure_time_seconds']
    stop_seq = gstop['stop_sequence']

    if prev_stop_loc is None:
      prev_stop_dist = None
      sched_travel_time = None
    else:
      prev_stop_dist = gis.distance_meters(prev_stop_loc,stop_loc);
      cumulative_dist += prev_stop_dist
      if prev_stop_depart is None:
        sched_travel_time = stop_arrive - prev_stop_arrive
      else:
        sched_travel_time = stop_arrive - prev_stop_depart

    db.export_trip_stop_information(trip_id,stop_seq, i, 
                                    prev_stop_dist,cumulative_dist,
                                    sched_travel_time);

    prev_stop_loc = stop_loc
    prev_stop_arrive = stop_arrive
    prev_stop_depart = stop_depart

  return cumulative_dist


### Autopopulation of routeid_dirtag table ###

def auto_populate_rid_dirtags():
  """
  Automatically determines matchup between dirtags and route ID's.
  This is done by joining the GPS tracking data table's routetag
  field with the GTFS route table's route_short_name field.  
  This just calls a database function.
  """
  db.populate_routeid_dirtag(True);
  db.commit()
  


### main ###


if __name__=="__main__":
  from os import sys
  if len(sys.argv) <= 1:
    print "Usage: %s cmd" %(sys.argv[0],)
    print " where cmd (and its effect) is one of the following:"
    print """  trips -- populates the trip information
               populate_ridtags -- autopopulates route_id/dirtag matchup
               match_trips -- match gtfs<-> gps trips
               gps_schedules -- from gps trips find actual schedules
               fix_earlybirds -- fix too-early gps trips
          """
    sys.exit(0)
  arg = sys.argv[1]
  if arg == 'trips':
    populate_all_trip_information()
  elif arg == 'match_trips':
    load_and_cache_routes(db.get_route_names())
  elif arg == 'gps_schedules':
    create_all_actual_timetables()
  elif arg == 'fix_earlybirds':
    fix_all_earlybirds()
  elif arg == 'populate_ridtags':
    auto_populate_rid_dirtags()
