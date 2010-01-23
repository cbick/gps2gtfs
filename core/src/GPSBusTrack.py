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

import dbqueries as db
import math
from BusTrack import BusTrack
from GTFSBusTrack import GTFSBusSchedule,GTFSBusTrack
import GPSDataTools as gpstool
import gisutils as gis


class GPSSchedule(object):
  """
  A lighter version of the GPSBusSchedule below, this class just 
  loads arrival time data as cached in the database (the results 
  from a GPSBusSchedule matchup).
  """
  def __init__(self,segment_id):
    """
    Loads segment_id's gps schedule from database
    """
    self.arrival_schedule = db.load_gps_schedule(segment_id);
    self.trip_id, self.trip_date, self.vehicle_id, self.schedule_error, \
        self.schedule_offset = db.load_gps_segment_header(segment_id);

  def getNumTimePoints(self,arrival_schedule=None):
    """
    """
    if arrival_schedule is None:
      arrival_schedule = self.arrival_schedule
    def help(a,b):
      if b['actual_arrival_time_seconds'] is None:
        return a
      return a+1
    return reduce(help,arrival_schedule,0)
    

  def getEarlyAndLateMeans(self,arrival_schedule=None):
    """
    Returns (mu_e,mu_l)
    where mu_e = mean of all early arrival times
    and   mu_l = mean of all late arrival times.

    Can optionall specify a static arrival schedule to calculate.
    """
    mu_e,mu_l=0.0,0.0
    n_e,n_l=0,0
    if arrival_schedule is None:
      arrival_schedule = self.arrival_schedule

    for arrival in arrival_schedule:
      arrival_time=arrival['actual_arrival_time_seconds'];
      if arrival_time is not None:
        sched_time = arrival['arrival_time_seconds']
        diff = arrival_time - sched_time
        if diff < 0: 
          mu_e -= diff
          n_e += 1
        elif diff > 0:
          mu_l += diff
          n_l += 1

    n_e = max(n_e,1)
    n_l = max(n_l,1)
    return mu_e/n_e, mu_l/n_l

  

class GPSBusSchedule(object):
  """
  A GPSBusSchedule object represents the actual arrival times of a
  GPS-tracked bus at its stops as described in the matching GTFS schedule.
  This class also serves as a central source for GTFSBusSchedule, 
  GPSBusTrack, and GTFSBusTrack objects.
  """
  def __init__(self,segment_id,trip_id=None,offset=None):
    """
    Creates a schedule matchup based on the specified tracked segment.
    If trip_id is specified, uses the GTFS schedule for that trip ID,
    otherwise uses the trip ID specified in the database.
    If offset is specified, then that offset is applied against GTFS
    data, otherwise the offset specified in the database is used.
    """
    self.segment = gpstool.TrackedVehicleSegment(segment_id,
                                                 useCorrectedGTFS=False);

    if offset is not None: 
      self.segment.offset = offset

    if trip_id is not None:
      self.segment.trip_id = trip_id;
      self.segment.schedule = GTFSBusSchedule(trip_id,self.segment.offset);
      
    self.schedule = self.segment.schedule;
    self.bustrack = GPSBusTrack(self.segment);

    self.corrected_schedule = None; #don't make it 'til someone wants it
    self.__matchSchedule();


  def getGTFSSchedule(self):
    return self.schedule;

  def getGPSSchedule(self):
    return self.arrival_schedule;

  def getGPSBusTrack(self):
    return self.bustrack;

  def getGTFSBusTrack(self, use_shape = False):
    if self.corrected_schedule is None:
      self.corrected_schedule = GTFSBusTrack(self.segment.trip_id,
                                             self.segment.offset,
                                             use_shape = use_shape);
    return self.corrected_schedule;


  


  def __matchSchedule(self):
    """
    Finds actual arrival times for each stop in the GTFS schedule
    """
    sched = []
    lasttime = self.segment.min_time
    prev_arrival_time = None
    prev_stop_id = None

    for stop,interp in zip(self.schedule.stops,self.schedule.interpolation):
      lat,lon = interp[:2]

      arrival_time = self.bustrack.getArrivalTimeAtLocation(
        stoploc=(lat,lon),
        tol=150.0, # meters
        starttime = lasttime);

      if arrival_time is None:
      #  print "NO ARRIVAL FOUND FOR STOP AT %d" %(time,)
        pass
      else:
      #  print "arrival for stop at %d" %(time,)
        if str(arrival_time) == 'nan':
          raise Exception, "asdf"
        lasttime = arrival_time;

      entry = dict(stop)
      entry['arrival_time_seconds'] = interp[2]
      entry['departure_time_seconds'] = stop['departure_time_seconds']\
                                         - self.schedule.offset
      entry['actual_arrival_time_seconds'] = arrival_time
      if None not in (arrival_time,prev_arrival_time):
        entry['seconds_since_last_stop'] = arrival_time - prev_arrival_time
      else:
        entry['seconds_since_last_stop'] = None
      entry['prev_stop_id'] = prev_stop_id;

      sched.append( entry );
      prev_arrival_time = arrival_time
      prev_stop_id = entry['stop_id'];

    self.arrival_schedule = sched;



class GPSBusTrack(BusTrack):
  """
  A BusTrack which interpolates the bus route between recorded
  lat/lon points from a GPS log.
  """
  
  def __init__(self,vehicle_segment):
    """
    Given a VehicleSegment, builds the interpolation.
    """
    self.__load(vehicle_segment);
    BusTrack.__init__(self);

  def __load(self, segment):
    self.segment = segment;
    self.reports = segment.reports

  def _loadInterpolation(self):
    ## WARNING: assumes no bus runs more than 24 hours
    p0 = self.reports[0];
    p0 = (float(p0.lat), float(p0.lon), p0.timeInSecondsIntoDay());
    last_pt = p0;
    interp = [p0];

    for vrep in self.reports[1:]:
      pt = [float(vrep.lat), float(vrep.lon), vrep.timeInSecondsIntoDay()]
      if pt[2] < p0[2]:
        if pt[2]-last_pt[2]+(24*60*60) > 600:
          print "## WARNING: JUMP FROM %d to %d" % (last_pt[2],pt[2]+24*60*60)
        pt[2] += 24*60*60; # We're moving into the next day
      if tuple(pt) == last_pt:
        continue
      last_pt = tuple(pt)
      interp.append(last_pt);

    return interp;


  def findLaunchTime(self,tol=50):
    """
    Finds the time that the bus moved tol meters from start point.
    If there is no shape data, then the start point is the first
    point in the dataset. Otherwise, the start point is defined by
    the first point in the shape. In this case, we first find the 
    time that the bus arrived at the start point, then search for
    the launch from there.
    """
    if self.segment.shape:
      arrived = False
      begin_pt = self.segment.shape.points[0];
    else:
      arrived = True
      begin_pt = self.interpolation[0][:2];
    for i,interp_pt in enumerate(self.interpolation):
      dist = gis.distance_meters(begin_pt,interp_pt[:2]);
      #print i,"dist:",dist
      if not arrived and dist <= tol:
        print "arrived at",interp_pt[2],"(%d steps)..."%(i,),
        arrived = True
      elif arrived and dist > tol:
        print "launched at",interp_pt[2]
        return interp_pt[2];
    return None

  def getMatchingGTFSTripID(self,search_size=20,oob_threshold=0.5):
    """
    Returns (tid,offset,error), or None if no matches are found

    Where tid is the GTFS trip_id for the trip which best matches
    the trip represented by this interpolation, offset is the offset
    in seconds to apply to the GTFS schedule to normalize according
    to 24 hour times, and error is the distance as measured from the
    GTFS trip.

    search_size indicates how many guesses to look at from
    gtfs schedule data, from which the best match is chosen.

    oob_threshold indicates the maximum fraction of the gtfs time 
    window for which this gps route is allowed to not exist in order 
    for that gtfs trip to be a candidate for a match.
    """
    start_date = self.reports[0].reported_update_time.date();
    start_time = self.findLaunchTime();
    if start_time is None:
      return None
    route_id,dir_id = self.segment.getGTFSRouteInfo();
    
    matches = db.get_best_matching_trip_ID(route_id,dir_id,start_date,
                                           start_time,num_results=search_size);
    print "Route %s (%s) launched at %d on %s" % \
        (route_id,dir_id,start_time,start_date)
    # dts is a list of ( (trip_id,offset_seconds), (distance,oob_frac) ) tuples
    dts = map( lambda r: \
                 (r,
                  self.measureDistanceFromGTFSTrip(r[0],r[1],
                                                   penalize_gps_oob=True,
                                                   penalize_gtfs_oob=False)
                  ),
               matches );
    # We want to filter out trips that are too far away from our
    # time window, and from there, return the trip with the 
    # minimum distance metric.
    dts = filter(lambda dt: dt[1][1] <= oob_threshold, dts);
    if len(dts) == 0:
      print "@@@ NO MATCHES FOUND WITHIN TIME WINDOW @@@"
      return None
    ret_index = dts.index(min(dts,key=lambda dt:dt[1][0]));
    return dts[ret_index][0][0],dts[ret_index][0][1],dts[ret_index][1][0];


  def measureDistanceFromGTFSTrip(self,trip_id,
                                  offset_seconds=0,
                                  penalize_gps_oob=True,
                                  penalize_gtfs_oob=True):
    """
    Given a GTFS Trip ID and an offset in seconds, returns
    
    (distance, oob_frac)

    where dist measures the distance of this trip from that one 
    as described below, and oob_frac is the fraction of scheduled
    stops (out of total number of stops) whose times are outside 
    the time window of this GPS segment.

    The penalize_xxx_oob parameters are used to indicate whether
    to penalize for special out-of-bounds cases. See below for details.
    
    Let n = # of timepoints for the GTFS trip
    For each timepoint T_i in the GTFS trip, let
      G(T_i) = location of GTFS scheduled stop at T_i
      B(T_i) = location of GPS signal at T_i+offset_seconds
    
    Then this function will return as the distance
      Sqrt( 1/n * Sum over i=1:n of Distance[G(T_i),B(T_i)]**2 )
    
    Note that the normalization factor of 1/n is necessary
    to prevent favoring of shorter routes.

    Typically the offset will be set to 86400 (24 hours) in cases
    where the GTFS trip is a "late night" (after midnight) schedule
    which means its times will be greater than 86400 (in seconds).


    The 'penalize_xxx_oob' parameters are used to determine what special
    treatment will be given to cases where bounding time window of
    the GPS trip is not well-matched to that of the GTFS trip. 
    (That is, whether or not to penalize periods of time where the gtfs 
    or gps data is "out of bounds" of the other).

    This breaks down into two basic cases:

    1. Periods of time where GPS data exists but the GTFS schedule does not.
       That is, the GPS data is out of bounds of the GTFS time window.
    
    2. Periods of time where the GTFS trip has schedule data but the GPS
       trip does not. That is, the GPS trip starts after the GTFS schedule,
       and/or it ends before the GTFS schedule, and so the GTFS data is
       out of bounds of the GPS time window.

    If penalize_gtfs_oob is False, then for periods where the GTFS trip 
    exists but the GPS trip does not, the GTFS is truncated to match the
    GPS time window. Otherwise, it is not truncated.

    If penalize_gps_oob is False, then for periods where the GPS trip exists
    but the GTFS trip does not, the GPS trip is truncated to match the GTFS
    time window. Otherwise, it is not truncated.

    The costs for non-truncated out-of-bound segments are handled as follows:

    - For timepoints T_i where GTFS exists and GPS does not, the distance
      between them is measured as though the GPS was found at the location
      of its first (or last) point. That is, if there is a GTFS timepoint
      before the beginning of the GPS trip, we use the first point in the
      GPS trip; if there is a GTFS timepoint after the end of the GPS trip,
      we use the last point in the GPS trip.

    - For cases where GPS exists and GTFS does not, we fabricate evenly
      spaced time points T_k for k = 1 to n, where 
    
      n = (GTFS_stops / GTFS_time) * GPS_OOB_time
      GTFS_time = time span of GTFS trip
      GTFS_stops = number of stops in GTFS trip
      GPS_OOB_time = amount of time GPS trip exists before/after GTFS trip

      For each of this times T_k the GTFS location is calculated as for
      the GPS trip in the case above. 

    This is used, for example, in a case where the GPS signal was 
    turned on several minutes late into the trip, the trip can match 
    very well with the GTFS schedule during that time the signal
    is alive, but during the beginning of the GTFS schedule
    there is no data. 

    In other cases, the GPS signal has been turned on several minutes
    early, before it has even arrived at the beginning of its route.

    You may wish to penalize this kind of behavior, or ignore it.

    WARNING: if penalize_gtfs_oob=False and penalize_gps_oob=False, 
    then the distance returned from this route with a GTFS trip 
    with no overlap in time will be 0!
    """
    schedule = GTFSBusSchedule(trip_id);
    #'bounding boxes' of our time interval and of the GTFS trip's time interval
    bbox = self.getRouteTimeInterval(); 
    sched_bbox = schedule.getRouteTimeInterval();
    oob_count = 0 #count of gtfs stop times that are out of bounds
    vstops = 0 #number of virtual stops that we penalized for

    ret = 0.0
    

    if penalize_gps_oob:
      ## To penalize for being too far outside the GTFS window,
      ## we need to calculate a number of "virtual stops" for which
      ## we were outside of that window, based on the number of stops
      ## the GTFS schedule makes in its time window.
      ## For each of these virtual stops, we penalize the square of
      ## the distance from our position at that time, to the closest-
      ## in-time position of the GTFS trip.
      
      # We use the total number of stops in the GTFS schedule divided
      # by the length in time of the schedule to approximate how many
      # virtual stops we should penalize for.
      stops_per_time = len(schedule.interpolation)/float(sched_bbox[1]
                                                         -sched_bbox[0])
      # If we start before the GTFS trip
      if bbox[0] < sched_bbox[0]:
        # oob_box is the out-of-bounds window
        oob_box=( bbox[0] , min(sched_bbox[0],bbox[1]) )
        # oob_time is the time spent out of bounds
        oob_time = oob_box[1] - oob_box[0]
        # loc1 is the starting location of the GTFS trip
        loc1 = schedule.interpolation[0][:2];
        # n is the number of 'virtual stops' we're penalizing for
        n = int( stops_per_time * oob_time );
        for i in range(n):
          T_i = bbox[0] + i * float(oob_time)/n
          loc2 = self.getLocationAtTime(T_i);
          if not loc2: print "ERROR SOMETHING IS TERRIBLY WRONG"
          ret += gis.distance_meters(loc2[:2],loc1)**2
        vstops += n


      # If we end after the GTFS trip
      if bbox[1] > sched_bbox[1]:
        # oob_box is the out-of-bounds window
        oob_box=( max(sched_bbox[1],bbox[0]) , bbox[1] )
        # oob_time is the time spent out of bounds
        oob_time = oob_box[1] - oob_box[0]
        # loc1 is the ending location of the GTFS trip
        loc1 = schedule.interpolation[-1][:2]
        # n is the number of 'virtual stops' to penalize for
        n = int( stops_per_time * oob_time );
        for i in range(n):
          T_i = bbox[1] - i * float(oob_time)/n
          loc2 = self.getLocationAtTime(T_i);
          if not loc2: print "ERROR SOMETHING IS TERRIBLY WRONG 2"
          ret += gis.distance_meters(loc2[:2],loc1)**2
        vstops += n


    ## Now check along the GTFS route
    for i,pt in enumerate(schedule.interpolation):
      stoptime = pt[2] - offset_seconds
      myloc = self.getLocationAtTime(stoptime);
      if myloc is None: # then GTFS is out of bounds of GPS time window
        oob_count += 1
        if penalize_gtfs_oob: # so penalize for it, if we're supposed to
          if stoptime < bbox[0]:
            myloc = self.interpolation[0]
          else:
            myloc = self.interpolation[-1]
      if myloc:
        ret += gis.distance_meters( myloc[:2], pt[:2] )**2

    ret = math.sqrt( ret/(len(schedule.interpolation)+vstops) )
    print "  Matching id",trip_id,"start time:",
    print schedule.interpolation[0][2]-offset_seconds,
    print "  distance: %9.2f OOB count: %2d/%2d"%(ret,oob_count,
                                                  len(schedule.interpolation))
    return ret,float(oob_count)/len(schedule.interpolation)

 
if __name__ == "__main__":
  route = Route(argv[1])
  gen_kml(route)

