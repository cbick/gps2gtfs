"""
BusTrack.py: Interface definition for a BusTrack object

"""

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
#


import gisutils as gis
from math import sqrt

class BusTrack(object):
  """
  Represents the continuous-time movement of a single bus along
  a single route. Different implementations may construct interpolations
  in different manners.
  """

  def __init__(self):
    self.cached_index = 0;
    self.interpolation = self._loadInterpolation();
    self.bounding_box = self._findBoundingBox();
    if self.interpolation:
      self.min_time = self.interpolation[0][2];
      self.max_time = self.interpolation[-1][2];

  def _findBoundingBox(self):
    """
    A private method which returns the tuple 
    (min_lon, max_lon, min_lat, max_lat) 
    representing the latitudinal and longitudinal bounds 
    that contain all points along this route.
    """
    if self.interpolation is None:
      return None
    initial = (1000,-1000,1000,-1000);
    def helper(bounds,point):
      lat,lon = map(float,(point[0],point[1]))
      return (min(bounds[0],lat), max(bounds[1], lat), 
              min(bounds[2],lon), max(bounds[3], lon));
    
    return reduce(helper, self.interpolation, initial);

  def _loadInterpolation(self):
    """
    A private method meant to be overridden by subclasses, which returns
    a list of (lat,lon,time) tuples, sorted by time. This list of tuples
    represents points along the bus movement.
    """
    raise Exception, "Unimplemented"

  def _interpolate(self,pt0,pt1,time):
    """
    A private method meant to be overridden by subclasses, which returns
    a (lat,lon) indicating the estimated position of the vehicle at the
    given time, provided that time lives between pt0 and pt1.
    pt0 and pt1 are each (lat,lon,time) tuples.

    The implementation below is a simple linear interpolation.
    """
    (lat0,lon0,time0) = pt0
    (lat1,lon1,time1) = pt1
    # same time different place?
    if time1 == time0:
      return (lat1+lat0)/2,(lon1+lon0)/2
    ratio = float(time-time0)/(time1-time0)
    dlat,dlon = (lat1-lat0),(lon1-lon0)
    return (lat0 + dlat*ratio, lon0 + dlon*ratio)


  def getLocationAtTime(self,time):
    """
    Given a time, returns a (lat,lon) location of the (estimated)
    location of the bus at that time. If the time is before or after
    the bounding time of the route, then None is returned.
    """
    if time < self.min_time or time > self.max_time:
      return None
    if time < self.interpolation[self.cached_index][2]:
      self.cached_index = 0    
    
    # Since time is within our bounds, this won't violate 
    # the bounds of our list
    while time > self.interpolation[self.cached_index+1][2]:
      self.cached_index += 1
    
    pt0 = self.interpolation[self.cached_index]
    pt1 = self.interpolation[self.cached_index+1]
    
    return self._interpolate( pt0, pt1, time );


  def getArrivalTimeAtLocation(self,stoploc,tol=10.0,starttime=None):
    """
    Given a stop location (lat,lon), a tolerance in meters, and a starting
    time, does the following:
    
    Finds the first time interval (t1,t2) within which the line segments
    of this track are all within tol meters of stoploc, and t1>starttime.
    
    Returns the time t such that t1<=t<=t2 at which this track was closest
    to stoploc.

    If this track was never within tol meters of the location, then 
    returns None.
    """
    ## We'll use the internal cached index here, just as in the
    ## getLocationAtTime method, in order to speed up sequential
    ## requests to this method.

    # Some might consider this bad programming practice,
    # in that we rely on the behavior of another method
    # to correcty implement this one.
    # If this ends up causing breakage, then there should
    # be some kind of "setInternalTime()" method for this class.
    if starttime is None: starttime = self.min_time;
    starttime = max(starttime,self.min_time);
    if starttime > self.max_time:
      return None

    startloc = self.getLocationAtTime(starttime);
    ll1 = startloc
    ll2 = self.interpolation[self.cached_index+1][:2]
    min_dist,frac = gis.interp_helper(ll1,ll2,stoploc);
    min_time = gis.timefrac_helper(starttime,
                               self.interpolation[self.cached_index+1][2],
                               frac);
    within_tol = (min_dist < tol);
    if str(min_time) == 'nan':
      raise Exception, "WTF"

    for idx in range(self.cached_index+1, len(self.interpolation)-1):
      pt1 = self.interpolation[idx];
      pt2 = self.interpolation[idx+1];
      ll1 = pt1[:2]
      ll2 = pt2[:2]
      dist,frac = gis.interp_helper(ll1,ll2,stoploc);
      
      if dist < min_dist:
        min_dist = dist;
        min_time = gis.timefrac_helper(pt1[2],pt2[2],frac);
        if str(min_time) == 'nan':
          raise Exception, "WTF"

      if (dist > tol) and within_tol:
        #We've left the tolerance zone, so we should have an answer
        break

      if (dist > tol):
        # We haven't found the tolerance zone yet
        continue

      within_tol = True;
      

    if not within_tol:
      # We never entered a tolerance zone
      print "XXX No arrival, min dist was:",min_dist
      return None  
    
    print "OOO Arrival with distance:",min_dist
    return min_time
    
    

  def getTimesAtLocation(self,stoploc,tol=10.0,starttime=None,findjustone=False):
    """
    Given a (lat,lon), returns a list of (begin,end,dist) intervals of the
    (estimated) times that the bus was within tol meters of that
    location, starting at starttime. The 'dist' part of each interval 
    indicates the estimated minimum distance of the bus from stoploc during 
    that interval.

    If starttime is None, then defaults to the beginning of the track.

    If findjustone is True, returns after finding the first complete interval.
    """
    in_range = False
    current_interval = None # will be [begin,end,dist] holder
    ret = []

    if starttime is None: starttime = self.min_time;
    starttime = max(starttime,self.min_time);
    if starttime > self.max_time:
      return ret

    ## Process intersection at first sub-segment
    startloc = self.getLocationAtTime(starttime);
    ll1 = startloc
    ll2 = self.interpolation[self.cached_index+1][:2]
    t1,t2 = starttime, self.interpolation[self.cached_index+1][2]
    overall_min_dist = gis.distance_from_segment_meters( ll1, ll2, stoploc )
    intersect = gis.distance_intersect( ll1, ll2, stoploc, tol )

    if intersect:
      enter_frac,exit_frac,min_dist = intersect
      enter_time = gis.timefrac_helper( t1,t2,enter_frac )
      exit_time = gis.timefrac_helper( t1,t2,exit_frac )
      if exit_frac == 1.0:
        current_interval = [ enter_time, exit_time, min_dist ]
        in_range = True
      else:
        ret.append([ enter_time, exit_time, min_dist ])

    ## Process subsequent segments
    for i in range(self.cached_index+1, len(self.interpolation)-1):
      llt1 = self.interpolation[i]
      llt2 = self.interpolation[i+1]
      ll1,ll2 = llt1[:2],llt2[:2]

      if len(ret) > 0 and findjustone:
        return ret

      overall_min_dist = min( overall_min_dist, 
                              gis.distance_from_segment_meters(ll1,ll2,stoploc))

      intersect = gis.distance_intersect( ll1,ll2,stoploc,tol )
      if intersect is None:
        if in_range:
          ret.append(current_interval)
          in_range = False
          current_interval = None
        else:
          pass

      else: # intersect is not None
        enter_frac,exit_frac,min_dist = intersect
        enter_time = gis.timefrac_helper( llt1[2],llt2[2],enter_frac )
        exit_time  = gis.timefrac_helper( llt1[2],llt2[2],exit_frac )

        if not in_range: # just entered range of stoploc
          if exit_frac == 1.0:
            current_interval = [ enter_time, exit_time, min_dist ]
            in_range = True
          else:
            ret.append([ enter_time, exit_time, min_dist ])

        else: # in_range
          if enter_frac != 0.0:
            raise Exception, "While in range, found enter_frac of %f" % (enter_frac,)
          else:
            current_interval[1] = exit_time
            current_interval[2] = min(current_interval[2],min_dist)
            if exit_frac == 1.0: # we're still in range
              pass
            else:
              ret.append( current_interval )
              in_range = False
              current_interval = None

    else: # end "for i in range..."
      if in_range:
        ret.append(current_interval)
    
    if not ret: # empty list
      print "--- No arrival, min dist was:",overall_min_dist

    return ret



  def getRouteTimeInterval(self):
    """
    Returns the (begin,end) times for which this BusTrack exists.
    """
    return (self.min_time, self.max_time);

  def getBoundingBox(self):
    """
    Returns (lonmin,lonmax,latmin,latmax) the lat/lon bounds
    of this route's traversal.
    """
    return self.bounding_box;

  def set_attributes(self,dictlike):
    """Sets attributes as, for each key in dictlike,
    self.key = dictlike[key]
    """
    for key in dictlike.keys():
      self.__setattr__(key,dictlike[key]);

