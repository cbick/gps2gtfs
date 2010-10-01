"""

"""

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
    Updates history with GPSDataTools.VehicleReport vreport.
    """
    self.track.append(vreport)
    
    if vreport.route_tag != self.last_routetag \
          or vreport.dirtag != self.last_dirtag:

      veh_seg = GPSDataTools.VehicleSegment(self.track)
      bustrack = GPSBusTrack.GPSBusTrack(veh_seg);
      gtfsinfo = bustrack.getMatchingGTFSTripID();

      if not gtfsinfo:
        print "Segment ended but no GTFS trip found (%d interp pts)" \
            % ( len(self.track), )
        print " Old route tag: %s, Old dir tag: %s" \
            % (self.last_routetag, self.last_dirtag)
        print " GPS Track:"
        print "  " + "\n  ".join(self.track)

      self.last_routetag = vreport.route_tag
      self.last_dirtag = vreport.dirtag
        
      return gtfsinfo
    
    return None






class RealtimeSimulation(object):
  """
  
  """
  
  def __init__(self, announce_callback = lambda trip, track: None):
    self.vehicles = {}
    self.announce = announce_callback

  def updateVehicles(self):
    update = route_scraper.get_updated_routes(None)
    for vehicle in update:
      vid = vehicle['id']
      now = vehicle['retrieve_time'] #datetime
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
      if gtfs_match is not None:
        self.announce( trip = gtfs_match, track = trk.getTrack() )
      

  def run(self):
    while True:
      self.updateVehicles()


