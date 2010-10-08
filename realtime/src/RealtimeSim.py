"""

"""

from os import path,sys  
mydir = path.abspath(path.dirname(sys.argv[0]))
coredir = mydir + "/../../core/src/"
sys.path.append(coredir)
sfmtadir = mydir + "/../../nextmuni_import/src/"
sys.path.append(sfmtadir)

import GPSDataTools
import GPSBusTrack
import datetime
import route_scraper


class GPSTrackState(object):
  """
  
  """
  def __init__(self, vehicle_id):
    self.vehicle_id = vehicle_id
    self.track = []
    self.last_routetag = None
    self.last_dirtag = None

  def getTrack(self, reversed = False):
    """
    Returns track history in list. If reversed is
    False, order is from oldest to newest. Otherwise,
    newest to oldest.
    """
    if reversed:
      return list(self.track.__reversed__())
    else:
      return list(self.track)


  def updateTrack(self, vreport):
    """
    Updates history with GPSDataTools.VehicleReport vreport. If the 
    vehicle changes routes, the last set of reports for the previous 
    route are collected into a GPSBusTrack.GPSBusTrack, and a
    GTFS match is attempted.

    If no GTFS match is discovered, or the vehicle didn't change
    routes, returns None.

    Otherwise, returns ( (trip_id,offset,error), segment_id )
      where (trip_id, offset, error) are the gtfs matchup info
      as returned by GPSBusTrack.getMatchingGTFSTripID(),
      and segment_id is the 
    """
    if self.track and vreport == self.track[-1]:
      return None
    
    ret = None

    if self.track and (vreport.route_tag != self.last_routetag \
                         or vreport.dirtag != self.last_dirtag):
      veh_seg = GPSDataTools.VehicleSegment(self.track)
      segment_id, gtfsinfo = veh_seg.export_segment()

      if gtfsinfo is None and len(self.track) > 1:
        print "Segment ended but no GTFS trip found (%d interp pts)" \
            % ( len(self.track), )
        print " Old route tag: %s, Old dir tag: %s" \
            % (self.last_routetag, self.last_dirtag)
        print " GPS Track:"
        print "  " + "\n  ".join(map(str,self.track))
      
      elif gtfsinfo is not None:
        ret = gtfsinfo, segment_id

      self.last_routetag = vreport.route_tag
      self.last_dirtag = vreport.dirtag
      self.track = []

    
    self.track.append(vreport)
    return ret






class RealtimeSimulation(object):
  """
  
  """
  
  def __init__(self):
    self.vehicles = {}

  def updateVehicles(self, xml = None):
    if xml is None:
      update = route_scraper.get_updated_routes(None)
    else:
      update = route_scraper.parse_xml(routes=None,xmldata=xml)

    for vehicle in update:
      vid = vehicle['id']
      now = vehicle['update_time'] #datetime
      delay = datetime.timedelta(seconds=int(vehicle['secsSinceReport']))
      update_time = now-delay

      report = GPSDataTools.VehicleReport(
        id = vid,
        lat = vehicle['lat'],
        lon = vehicle['lon'],
        routetag = vehicle['routeTag'],
        dirtag = vehicle['dirTag'],
        reported_update_time = update_time
        );
      
      trk = self.vehicles.get( vid )
      if not trk:
        trk = GPSTrackState(vid)
        self.vehicles[vid] = trk

      gtfs_match = trk.updateTrack(report)
      return gtfs_match
