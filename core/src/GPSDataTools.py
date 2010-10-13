"""
GPSDataTools.py: Utilities and class definitions for dealing with raw GPS 
tracking data.

In general one is only interested in the Route class, which loads GPS data 
from the database for a particular route and automatically turns it into 
individual trips.
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

import dbqueries as db
import datetime
from time import time
from sys import argv
from kml_objects import *
import math
from GTFSBusTrack import GTFSBusSchedule,GTFSBusTrack
import gisutils as gis

rad = math.pi / 180.0

THRESH_SEG_ENDPOINT_TO_SHAPE_ENDPOINT = 50 #meters
THRESH_TIME_BETWEEN_REPORTS = 120 # seconds
THRESH_MINIMUM_REPORTS = 10

def now():
  return str(int(time()))


class VehicleReport(object):
  """
  POD structure representing a single row in the GPS log.
  """
  def __init__(self,id,lat,lon,routetag,dirtag,reported_update_time):
    self.vehicle_id = id
    self.lat = lat
    self.lon = lon
    self.route_tag = routetag
    self.dirtag = dirtag
    self.reported_update_time = reported_update_time

  def __str__(self):
    return """\
vehicle %s on route %s, dirtag %s:  %s, %s, time %s
""" % (self.vehicle_id, self.route_tag, self.dirtag,
       self.lat,self.lon,self.reported_update_time)

  def __eq__(self,other):
    return (self.vehicle_id, self.lat, self.lon, self.route_tag,
            self.dirtag, self.reported_update_time) \
            == (other.vehicle_id, other.lat, other.lon, other.route_tag,
                other.dirtag, other.reported_update_time)

  def dayOfWeek(self):
    """
    0123456 = MTWThFSSu
    """
    return self.reported_update_time.weekday()

  def timeInSecondsIntoDay(self):
    t = self.reported_update_time
    h,m,s = t.hour,t.minute,t.second
    return s + 60*( m + 60*h )

class VehicleSegment(object):
  """
  A list of VehicleReports, representing a single trip made by
  a vehicle.
  """
  def __init__(self,reports):
    self.reports = reports
    self.dirtag = reports[-1].dirtag
    self.routetag = reports[-1].route_tag
    self.lations = [[r.lat,r.lon] for r in reports]
    self.shape = None
    self.valid = True

  def getGTFSRouteInfo(self):
    """
    Returns (routeID,directionID) for this trip.
    """
    route_id = db.get_route_for_dirtag(self.dirtag, routetag = self.routetag);
    dir_id = db.get_direction_for_dirtag(self.dirtag);
    print "Dirtag",self.dirtag,"routetag",self.routetag,"matched to",
    print route_id,dir_id
    return (route_id,dir_id);

  def export_segment(self):
    """
    Exports this segment to the database.
    Returns ( segment_id, (trip_id,offset,error) ),
      where segment_id is the tracked_vehicle_segment ID as exported
      into the database,
      and (trip_id,offset,error) are the gtfs matchup info as returned
      by GPSBusTrack.getMatchingGTFSTripID(). 

    If no match is found, returns None.
    """
    from GPSBusTrack import GPSBusTrack
    segID = db.getMaxSegID()+1;
    bt = GPSBusTrack(self);
    tinfo = bt.getMatchingGTFSTripID();
    if tinfo is None:
      print "No GTFS trip found (%d interp pts)" % (len(self.reports),)
      trip_id,offset,error=None,0,0
    else:
      trip_id,offset,error = tinfo
    trip_date = self.reports[0].reported_update_time
    rows=[(r.lat,r.lon,r.reported_update_time) for r in self.reports]
    veh_id = self.reports[0].vehicle_id;
    db.export_gps_route(trip_id, trip_date, segID, veh_id, error, offset, rows);
    return segID, tinfo


class TrackedVehicleSegment(object):
  """
  A variation on the VehicleSegment class for segments which have
  already been identified with a GTFS trip ID and all the associated
  information.
  """
  def __init__(self,segment_id,useCorrectedGTFS=True):
    self.segment_id = segment_id;
    self.trip_id, self.trip_date, self.vehicle_id, self.schedule_error, \
        self.offset, self.route = db.load_gps_route(segment_id);

    self.reports = map(lambda llr: VehicleReport(self.vehicle_id,llr[0],llr[1],
                                                 None,None,llr[2]),
                       self.route);

    if self.trip_id is not None:
      if useCorrectedGTFS:
        self.schedule = GTFSBusTrack(self.trip_id, offset=self.offset,
                                     use_shape=False);
      else:
        self.schedule = GTFSBusSchedule(self.trip_id,offset=self.offset);

      self.route_id = self.schedule.route_id;
      self.dir_id = self.schedule.direction_id;

    else: #self.trip_id is None
      self.route_id = None
      self.dir_id = None
      self.schedule = None

    self.shape = None;
    self.min_time = self.reports[0].timeInSecondsIntoDay();
    self.max_time = self.reports[-1].timeInSecondsIntoDay();
    if self.max_time < self.min_time: self.max_time += 86400


  def getGTFSRouteInfo(self):
    """
    Returns (routeID,directionID) for this trip.
    """
    return self.route_id,self.dir_id;


    



class Vehicle(object):
  """
  Represents a uinque transit vehicle, as definted by its ID 
  in the vehicle_track table
  """  
  def __init__(self,vehicle_id):
    self.vehicle_id = vehicle_id;
    self.reports = []
    self.segments = []

class GShape(object):
  def __init__(self,id):
    self.id=id
    self.points=[]
    self.dirtag = ''

class Route(object):
  """
  Represents the set of vehicle trips belonging to a particular route.
  Upon initialization, all VehicleReports are found for that route,
  and subsequently segmented into appropriate VehicleSegments.
  """
  def __init__(self,route_short_name):
    self.route_short_name = str(route_short_name)
    self.dirtags=[]
    self.shapes = {}
    self._vehicles = {}
    
    print "Loading Dirtags..."
    self.load_route_dirtags()
    print "\t%s"% '\n\t'.join(self.dirtags)
    #print "\t%s" % ' '.join(self.dirtags)
    
    print "Loading Shapes..."
    self.load_shapes()
    print "\tLoaded %s shapes: %s" % (len(self.shapes),', '.join([ shape_id for shape_id,shape in self.shapes.items()]))
    
    
    
    self.load_vehicle_reports()
    print "\tFound %s vehicles" % len(self._vehicles)
    
    print "Finding route segments..."
    self.find_segments()
    
    
    if self.shapes:
      self.filter_by_endpoint()
    else:
      print "No shapes found, skipping shape check"
       
    self.filter_by_report_time()

    
  def load_route_dirtags(self):
    self.dirtags.extend(db.get_route_dirtags(self.route_short_name));
      

  def load_vehicle_reports(self):
    print "Loading vehicle reports..."
    rows = db.get_vehicle_reports(self.dirtags);
    print "\tDB fetch complete.  Sorting into objects.."

    def helper(row):
      vehicle_id = row['id']
      vehicle = self._vehicles.get(vehicle_id);
      if vehicle is None:
        vehicle = Vehicle(vehicle_id);
        self._vehicles[vehicle_id] = vehicle;
      vehicle.reports.append(VehicleReport(*row))

    map( helper, rows );

    
  def load_shapes(self):  
    rows = db.get_shapes_for_route(self.route_short_name);
    for row in rows:
      shape_id = row['shape_id']
      dirtag = row['dirtag']
      gshape = self.shapes.get(shape_id);
      if gshape is None:
        gshape = GShape(shape_id);
        gshape.dirtag = dirtag
        self.shapes[shape_id] = gshape
        self.dirtags.append(dirtag)
      gshape.points.append([row['shape_pt_lat'],row['shape_pt_lon']])


  def find_segments(self):
    for vehicle in self.vehicles():
      #print "\tSegmenting Vehicle %s..." % vehicle.vehicle_id
      reports=[]

      last_report = vehicle.reports[0]
      for report in vehicle.reports[1:]:
        if report.dirtag != last_report.dirtag:
          if len(reports) > THRESH_MINIMUM_REPORTS:
            seg = VehicleSegment(reports);
            seg.shape = self.shape_for_dirtag(seg.dirtag)
            vehicle.segments.append(seg);
          reports=[]
        reports.append(report)
        last_report = report
      #print "\t\t%s segments found" % len(vehicle.segments)
    print "\tFound %s segments" % len([s for s in self.segments()])
    print "\tRemoving vehicles that have no segments..." 
    c=0
    for vehicle in self.vehicles():
      if not vehicle.segments:
        c+=1
        del self._vehicles[vehicle.vehicle_id]
    print "\tRemoved %s vehicles"%c

  def filter_by_endpoint(self):
    print "Filtering segments by comparing segment endpoints to possible gtf_shape(s)..."
    c=0
    for seg in self.segments(return_valid_only=True):
      seg_start_lation = seg.lations[0]
      seg_end_lation = seg.lations[-1]

      s = seg.shape #self.shape_for_dirtag(seg.dirtag)
      if s is None:
        continue

      shape_start_lation = s.points[0]#.lation
      shape_end_lation = s.points[-1]#.lation

      start_point_distance = calcDistance(shape_start_lation,seg_start_lation)
      end_point_distance = calcDistance(shape_end_lation,seg_end_lation)

      if start_point_distance > THRESH_SEG_ENDPOINT_TO_SHAPE_ENDPOINT:
        seg.valid = False
        c+=1
      else:
        seg.valid = True
    print "\t%s marked as invalid" % c

  def filter_by_report_time(self):
    print "Filtering by comparing times between reports..."
    c=0
    for seg in self.segments(return_valid_only=True):
      last = seg.reports[0]
      avg=[]
      for r in seg.reports[1:]:
        t=int((r.reported_update_time - last.reported_update_time).seconds)
        avg.append(t)
        last = r
        if t > THRESH_TIME_BETWEEN_REPORTS:
          seg.valid = False
      if not seg.valid:
        c+=1
    print "\t%s marked invalid" % c   
               
  def segments(self,return_valid_only=False):
    sorted_vehicles = self._vehicles.items()
    sorted_vehicles.sort()
    for vid,vehicle in sorted_vehicles:
      for seg in vehicle.segments:
        if return_valid_only and seg.valid == False:
          continue
        else:
          yield seg

  def shape_for_dirtag(self,dirtag):
    for shape_id,shape in self.shapes.items():
      if shape.dirtag == dirtag:
        return shape
        
  def vehicles(self):
    sorted_vehicles = self._vehicles.items()
    sorted_vehicles.sort()
    for vid,vehicle in sorted_vehicles:
      yield vehicle

  def clear_filters(self):
    for seg in self.segments():
      seg.valid = True

  def export_segments(self,valid_only=True):
    segs = list(self.segments(valid_only));
    for i,seg in enumerate(segs):
      print "Exporting (%d/%d)..."%(i+1,len(segs))
      seg.export_segment();
        
        



def calcDistance(lation1,lation2):                      
    """
    Caclulate distance between two lat lons in meters
    """
    return gis.distance_meters( map(float,lation1), 
                                map(float,lation2) )

 
  
def gen_kml(route,dopoints=False,dotimestamps=False):
  print "Building KML.."
  
  #Pepare dirtag folders
  dirTagFolders = {}
  for tag in route.dirtags:
    dirTagFolders[tag] = {}#KFolder(tag)
  
  invalid_paths = KFolder('INVALID')
  for vehicle in route.vehicles():
    vehicle_folder = KFolder(vehicle.vehicle_id)
    
    for seg in vehicle.segments:
      if dopoints:
        point_folder = KFolder("points")
        point_folder.visibility = False
        
      folder = KFolder()
      folder.name = "#%03d %s - %s " % (vehicle.segments.index(seg),vehicle.vehicle_id,seg.dirtag)
      path = KPath()
      for r in seg.reports:
        l = [r.lat,r.lon]
        path.add(l)
        if dopoints:
          p=KPlacemark(KPoint(l),name=r.reported_update_time)
          p.visibility=False
          point_folder.add(p)
        
      folder.add(KPlacemark(path,folder.name,style_url='segmentLine'))
      
      if dopoints:
        folder.add(point_folder)
      
      if dotimestamps:
        folder.add(KPlacemark(KPoint(seg.lations[0]),name=seg.reports[0].reported_update_time,style_url='map_shaded_dot_true'))
        folder.add(KPlacemark(KPoint(seg.lations[-1]),name=seg.reports[-1].reported_update_time,style_url='map_shaded_dot_false'))
      else:
        folder.add(KPlacemark(KPoint(seg.lations[0]),name='',style_url='map_shaded_dot_true'))
        folder.add(KPlacemark(KPoint(seg.lations[-1]),name='',style_url='map_shaded_dot_false'))
      
      if seg.valid is True:
        if not dirTagFolders[seg.dirtag].has_key(vehicle.vehicle_id):
          dirTagFolders[seg.dirtag][vehicle.vehicle_id] = KFolder(vehicle.vehicle_id)
        dirTagFolders[seg.dirtag][vehicle.vehicle_id].add(folder)
      else:
        folder.visibility = False
        invalid_paths.add(folder)
  
  dir_folder = KFolder('Directions')
  sorted_dirs = dirTagFolders.items()
  sorted_dirs.sort()
  for dirtag,vfolders in sorted_dirs:
    dirFolder = KFolder(dirtag)
    for vid,vfolder in vfolders.items():
      dirFolder.add(vfolder)
    dir_folder.add(dirFolder)  
  
  main_document = KFolder('Route %s'%route.route_short_name)
  main_document.add(dir_folder)
  
  #Creaate a folder which draws the gtf_shape deifintions
  shape_folder = KFolder('Shapes')
  if route.shapes:
    for shape_id,shape in route.shapes.items():
      path = KPath()
      path.lations = [ l for l in shape.points]
      shape_folder.add(KPlacemark(path,name=shape_id,style_url='gShapeLine'))
    main_document.add(shape_folder)
    
  kml_doc = KDocument(template_path='kml/document.kml',
                        docname="Test %s" % now(),
                        fname="%s_segments.kml" % route.route_short_name,
                        top_object=main_document,
                        style_doc='kml/segment_find_styles.kml')
  print "Writing..."
  kml_doc.write()







 
if __name__ == "__main__":
  route = Route(argv[1])
  gen_kml(route)

