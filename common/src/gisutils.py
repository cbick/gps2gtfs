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

import math
import shapely.geometry as geom

def latlon_distance_conversion(lat):
  """
  Given a latitude (in degrees), returns (mperlat,mperlon)
  where mperlat = meters per degree latitude,
  mperlon = meters per degree longitude.
  These calculations are based on a spherical earth, and were taken from
  http://www.nga.mil/MSISiteContent/StaticFiles/Calculators/degree.html
  """
  lat_rad = lat * 2.0 * math.pi / 360.0;
  m1 = 111132.92;
  m2 = -559.82;
  m3 = 1.175;
  m4 = -0.0023;
  p1 = 111412.84;
  p2 = -93.5;
  p3 = 0.118;
  
  latlen = m1 + (m2 * math.cos(2 * lat)) + (m3 * math.cos(4 * lat)) + \
      (m4 * math.cos(6 * lat));
  lonlen = (p1 * math.cos(lat)) + (p2 * math.cos(3 * lat)) + \
      (p3 * math.cos(5 * lat));

  return (latlen,lonlen);


def distance_meters(ll1, ll2):
  """
  Given two (lat,lon) points ll1 and ll2, returns the distance
  between them in meters. Note that this only works for points
  that are relatively close.
  """
  lat1,lon1 = map(float,ll1)
  lat2,lon2 = map(float,ll2)
  midlat = (lat1+lat2)/2
  m_per_lat,m_per_lon = latlon_distance_conversion(midlat);

  lon_dist_m = (lon2-lon1)*m_per_lon;
  lat_dist_m = (lat2-lat1)*m_per_lat;

  return math.sqrt(lon_dist_m**2 + lat_dist_m**2);


def distance_nautical_miles(ll1,ll2):
  """
  Given two (lat,lon) points ll1 and ll2, returns the distance
  between them in nautical miles.
  """
  lat1,lon1=ll1
  lat2,lon2=ll2
  rad = math.pi / 180.0
    
  yDistance = (lat2 - lat1) #* nauticalMilePerLat
  xDistance = (math.cos(lat1 * rad) + math.cos(lat2 * rad)) * (lon2 - lon1)# * (nauticalMilePerLongitude / 2)
    
  distance = math.sqrt( yDistance**2 + xDistance**2 )
  
  return distance# * milesPerNauticalMile


def distance_from_line_meters(pt1,pt2,ll):
  """
  Given two (lat,lon) points pt1 and pt2 defining a line,
  and a third (lat,lon) point ll, returns the distance
  in meters of ll from the line.
  """
  raise Error, "Unimplemented"
  

def distance_from_segment_meters(pt1,pt2,ll):
  """
  Given two (lat,lon) endpoints of a line pt1 and pt2,
  and a third (lat,lon) point ll, returns the distance
  in meters of ll from the segment.
  """
  ## First convert to meter coordinates for proper distance
  lat1,lon1 = map(float,pt1)
  lat2,lon2 = map(float,pt2)
  llat,llon = map(float,ll)
  midlat = (lat1+lat2+llat)/3.
  midlon = (lon1+lon2+llon)/3.
  m_per_lat,m_per_lon = latlon_distance_conversion(midlat);
  ## Translate to the weighted center
  y1,x1 = (lat1-midlat)*m_per_lat,(lon1-midlon)*m_per_lon
  y2,x2 = (lat2-midlat)*m_per_lat,(lon2-midlon)*m_per_lon
  ly,lx = (llat-midlat)*m_per_lat,(llon-midlon)*m_per_lon
  ## Compute and return answer
  sh_line = geom.LineString(( (x1,y1) , (x2,y2) ))
  sh_pt = geom.Point(( lx,ly ))
  return sh_pt.distance(sh_line);

def interp_helper(ll1,ll2,pt):
  """
  Returns (distance,fraction)
  where distance = distance of p1 from ll1-ll2 segment, and 
  fraction = fractional progress of the minimum-distance point
  along the segment ll1->ll2
  """
  D_ps = distance_from_segment_meters(ll1,ll2,pt);
  D_12 = distance_meters(ll1,ll2);
  D_p1 = distance_meters(ll1,pt);
  if D_12 == 0:
    return D_p1,0.0
  if D_p1 < D_ps:
    return D_p1,0.0
  frac = math.sqrt( int(D_p1)**2 - int(D_ps)**2 ) / D_12;      
  return (D_ps,frac);

def timefrac_helper(t1,t2,frac):
  """
  Shorthand for t1 + (t2-t1)*frac, returns the number
  t whose fractional progress along t1->t2 is frac.
  """
  return t1 + (t2-t1)*frac;


def distance_intersect(ll1,ll2,pt,tol):
  """
  Returns (enter_frac,exit_frac,min_dist), where:
    enter_frac is the fractional progress of the first point 
      in ll1->ll2 within tol meters of pt; 
    exit_frac is the fractional progress of the last point 
      in ll1->ll2 within tol meters of pt;
    min_dist is the distance in meters from pt to the segment ll1-ll2.

  If the first or last endpoint is within tol meters of pt, then
  enter_frac or end_frac is guaranteed to be precisely 0.0 or
  1.0, respectively.

  Returns None if the ll1-ll2 segment has no points within
  tol meters of pt.
  """
  ## First convert to meter coordinates for proper distance
  lat1,lon1 = map(float,ll1)
  lat2,lon2 = map(float,ll2)
  ptlat,ptlon = map(float,pt)
  midlat = ptlat #(lat1+lat2+ptlat)/3.
  midlon = ptlon #(lon1+lon2+ptlon)/3.
  m_per_lat,m_per_lon = latlon_distance_conversion(midlat);
  ## Translate to the weighted center
  y1,x1 = (lat1-midlat)*m_per_lat,(lon1-midlon)*m_per_lon
  y2,x2 = (lat2-midlat)*m_per_lat,(lon2-midlon)*m_per_lon
  pty,ptx = (ptlat-midlat)*m_per_lat,(ptlon-midlon)*m_per_lon
  
  intersect_zone = geom.Point((ptx,pty)).buffer(tol,100)
  simple_point = geom.Point((ptx,pty))
  seg = geom.LineString(( (x1,y1) , (x2,y2) ))
  intersect = intersect_zone.intersection(seg);
  
  if intersect.is_empty:
    return None

  begin_pt, end_pt = geom.Point((x1,y1)), geom.Point((x2,y2))
  frac_a = geom.Point( intersect.coords[0] ).distance( begin_pt ) / seg.length
  frac_b = geom.Point( intersect.coords[1] ).distance( begin_pt ) / seg.length

  frac_1,frac_2 = min(frac_a,frac_b), max(frac_a,frac_b)
  if begin_pt.distance(simple_point) <= tol:
    frac_1 = 0.0
  if end_pt.distance(simple_point) <= tol:
    frac_2 = 1.0

  min_dist = simple_point.distance(seg)
  
  return (frac_1,frac_2,min_dist)
