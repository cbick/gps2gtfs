import dbqueries as db
import gisutils as gis
from BusTrack import BusTrack



class GTFSBusSchedule(BusTrack):
  """
  A BusTrack whose interpolation is mostly meaningless,
  but will return correct location for times listed
  in the GTFS schedule.
  """
  
  def __init__(self, trip_id,offset=0):
    """
    Given the GTFS trip_id, loads and constructs the schedule.
    Optionally, 'offset' seconds will be subtracted from each
    time in the schedule.
    """
    self.trip_id = trip_id
    self.offset = offset
    self.__load()
    BusTrack.__init__(self)

  def __eq__(self,other):
    return self.trip_id==other.trip_id and self.offset==other.offset;

  def __hash__(self):
    return hash(self.trip_id) * 7 - self.offset;

  ## Loads data about this trip from the database
  def __load(self):
    (trip_data,self.stops,self.shape) = db.getGTFSTripData(self.trip_id);
    self.set_attributes(trip_data);
    route_data = db.getGTFSRouteData(self.route_id);
    self.set_attributes(route_data);

  def _loadInterpolation(self):
    """
    Simply takes the GTFS schedule at face value and doesn't
    try to extract any more information out of it, nor apply
    any heuristics to it.
    """
    interpolation = []
    for stop in self.stops:
      interpolation.append( (stop['stop_lat'],
                             stop['stop_lon'],
                             stop['arrival_time_seconds']-self.offset));
      # If the bus sits there for a while, then add a point
      if stop['arrival_time_seconds'] != stop['departure_time_seconds']:
        interpolation.append( (stop['stop_lat'],
                               stop['stop_lon'],
                               stop['departure_time_seconds']-self.offset));
    return interpolation




class GTFSBusTrack(GTFSBusSchedule):
  """
  A BusTrack which interpolates the bus route along a 
  schedule defined by GTFS data, including the schedule
  and the shape (if provided).
  """

  def __init__(self,trip_id,offset=0,use_shape=True):
    """
    Given the GTFS trip_id, loads and constructs the object.
    Optionally, 'offset' seconds will be subtracted from every time
    in the trip.
    """
    self.use_shape = use_shape;
    GTFSBusSchedule.__init__(self,trip_id,offset);


  

  def findMatchingShapeIndex(self,stop,begin_idx=0,tol=20):
    ## Given a stop, finds the first shape segment at
    ## index i >= begin_idx that is within tol meters
    ## of the stop's location.

    last_pt = self.shape[begin_idx]
    min_dist,min_pt = 1e10,None
    for i,pt in enumerate(self.shape[begin_idx+1:]):
      dist = gis.distance_from_segment_meters( (last_pt['shape_pt_lat'],
                                                last_pt['shape_pt_lon']),
                                               (pt['shape_pt_lat'],
                                                pt['shape_pt_lon']),
                                               (stop['stop_lat'],
                                                stop['stop_lon']) );
      if dist <= tol:
        return i+begin_idx; #really it's i+begin_idx+1 - 1
      if dist < min_dist:
        min_dist,min_pt = dist,pt
      last_pt = pt
    print "Returning none (DOH!)"
    print "  Min dist was %f meters" % (min_dist,)
    return None


  def _loadInterpolation(self):
    ## The idea here is to put all the space/time information
    ## we have about this route into order so that we can make
    ## as good an interpolation as possible.
    ##
    ## First, we place the stops into the correct positions
    ## along the shape. Then from the times of the stops we can
    ## guess the times of the points on the shape.
    ##
    ## Note that if there is no shape_dist_traveled data available
    ## for the route, then there will probably be some large
    ## errors between some stops.
    
    # At the end of this, interpolation will be a list of
    # (lat,lon,time) tuples. This will be the basis of our final
    # representation.
    interpolation = []
    segment_idx = 0;

    if self.use_shape:
      segment = self.shape[0]
      interpolation = [  (segment['shape_pt_lat'],
                          segment['shape_pt_lon'],
                          None)  ];
    
    for stop in self.stops:
      # If we're using shape info we need to know where we are along it
      if self.use_shape:
        stop_segment_idx = self.findMatchingShapeIndex(stop,
                                                       begin_idx=segment_idx,
                                                       tol=50);
        if stop_segment_idx is None:
          print "Could not locate stop on shape within 50 meters"
          print " Route %s (%s), trip %s" % (self.route_short_name,
                                             self.route_id,
                                             self.trip_id)
          return

        while segment_idx < stop_segment_idx:
          segment_idx += 1
          segment = self.shape[segment_idx]
          interpolation.append( (segment['shape_pt_lat'],
                                 segment['shape_pt_lon'],
                                 None));

      # Regardless of shape use we put the stop into the interp
      interpolation.append( (stop['stop_lat'],
                             stop['stop_lon'],
                             stop['arrival_time_seconds']-self.offset));
      # If the bus sits there for a while, then add a point
      if stop['arrival_time_seconds'] != stop['departure_time_seconds']:
        interpolation.append( (stop['stop_lat'],
                               stop['stop_lon'],
                               stop['departure_time_seconds']-self.offset));

        
    # Finish up the rest of the shapes, if we're using them
    if self.use_shape:
      while segment_idx+1 < len(self.shape):
        segment_idx += 1
        segment = self.shape[segment_idx];
        interpolation.append( (segment['shape_pt_lat'],
                               segment['shape_pt_lon'],
                               None));
      
    # For debugging purposes
    self.preinterp = [interp for interp in interpolation];
    
    ## At this point we have some problems:
    ##    1) duplicate lat-lon pairs, in the case that a 
    ##       shape point matches with a stop point.
    ##    2) a bunch of tuples with a time value of None
    ##    3) sequences of points at different places but 
    ##       at the same time.
    ## We now endeavor to eliminate these problems, as follows:
    ##    1) Eliminate duplicate lat-lon pairs by keeping the element
    ##       which has time data. Duplicate lat-lon pairs where both
    ##       elements have a time are not eliminated.
    ##    2) Interpolate times for shape points between stop points.
    ##       If there are shape points at the begin/end with no times,
    ##       they will be given times 1 in second increments before/after 
    ##       the first/last stop points.
    ##    3) Interpolate sub-minute times for points occurring at different
    ##       places but at the same time.
    
    ## 1. Eliminate redundancies
    last_point = interpolation[0]
    for point in interpolation[1:]:
      if point[0] == last_point[0] and point[1] == last_point[1]:
        if not (point[2] or last_point[2]):
          print "Duplicate Shape Points????"
        elif not point[2]:
          interpolation.remove(point);
          continue; # don't want to set last_point to the removed one
        elif not last_point[2]:
          interpolation.remove(last_point);
        elif point[2] == last_point[2]:
          print "Duplicate Time Points????"
          interpolation.remove(last_point);
        else:  # point[2] != last_point[2]:
          pass # leave them both in
      last_point = point

    ## 2. Interpolate times for shape points (if we used them)
    if self.use_shape:
      last_timed_idx = None;
      last_timed = None;
      for i,point in enumerate(interpolation):
        # If there are points between here and last_timed that don't have times
        if point[2] and last_timed and i > last_timed_idx+1:
          #print"interpolating between times %d and %d"%(last_timed[2],point[2])
          delta_t = float(point[2] - last_timed[2]) / (i-last_timed_idx)
          interptime = last_timed[2]
          for j,untimed in enumerate(interpolation[last_timed_idx+1:i]):
            interptime += delta_t
            interpolation[j+last_timed_idx+1] = (untimed[0],untimed[1],interptime);
      
        if point[2]:
          if not last_timed:
            #Fabricate times for the first points
            for j in range(i):
              untimed = interpolation[j]
              interpolation[j] = (untimed[0],untimed[1],point[2] - (i-j));
          last_timed = point;
          last_timed_idx = i;
    
      # Now fabricate times for the last points
      for j in range(last_timed_idx+1,len(interpolation)):
        untimed = interpolation[j]
        interpolation[j] = (untimed[0], untimed[1], 
                            last_timed[2] + (j-last_timed_idx));

  
    ## 3. String out same-time-different-place stops across time
    begin_stop, begin_idx = None,None
    end_stop,end_idx = None, None
    for i,point in enumerate(interpolation):
      # if this is a new search for duplicate times
      if not begin_stop:
        begin_stop, begin_idx = point,i
      # if this is a duplicate time
      elif point[2] == begin_stop[2]:
        end_stop, end_idx = point, i
      # if there were no duplicate times
      elif not end_stop:
        begin_stop, begin_idx = point,i
      # if we reached the end of a string of duplicate times
      else:
        num_stops = i - begin_idx;
        # We will try to fit them all within their minute
        if (60 - (begin_stop[2] % 60)) < num_stops:
          raise Exception, "Too many (%d) duplicate times to eliminate"\
              %(num_stops,)
        for j in range(begin_idx+1,end_idx+1):
          pt = interpolation[j]
          interpolation[j] = (pt[0],pt[1],pt[2] + j - begin_idx);
        # Begin the next search
        begin_stop,begin_idx,end_stop = point,i,None

    # yay done
    return interpolation
    
