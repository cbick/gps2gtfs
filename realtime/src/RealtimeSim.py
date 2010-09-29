"""

"""

class linkring(object):
  """
  Doubly linked list ring of fixed length.
  Updates in rotating manner.
  """
  class linknode(object):
    def __init__(self,value):
      self.next = None
      self.prev = None
      self.value = value

  def __init__(self, len):
    self.ring = linkring.linknode(None)
    lastref = self.ring

    for i in range(len-1):
      tmp = linkring.linknode(None);
      tmp.next = self.ring
      self.ring.prev = tmp
      self.ring = tmp;

    lastref.next = self.ring
    self.ring.prev = lastref

  def update(self, value):
    """
    Insert new value into list
    """
    self.ring.value = value
    self.ring = self.ring.prev

  def __iter__(self):
    """
    Returns values in order from oldest to newest
    """
    yield self.ring.value
    next = self.ring.prev
    while next is not self.ring:
      yield next.value
      next = next.prev
      
  def __reversed__(self):
    """
    Returns values in order from newest to oldest
    """
    yield self.ring.next.value
    next = self.ring.next.next
    while next is not self.ring.next:
      yield next.value
      next = next.next

  @staticmethod
  def test():
    r = linkring(10)
    for i in range(10):
      r.update(i)
    print list(r)
    print list(r.__reversed__())


class RouteStop(object):
  """
  For a given route, direction and stop, this class
  represents the times at which the bus is scheduled
  to arrive.
  """
  def __init__(self, trip_id, stop_id):
    self.trip_id = trip_id
    self.stop_id = stop_id
    self.schedule = self.loadSchedule()

  def loadSchedule(self):
    return []


class GPSTrackState(object):
  """

  """
  def __init__(self, vehicle_id, history_len):
    self.len = history_len
    self.vehicle_id = vehicle_id
    self.track = linkring(self.len)

  def getTrack(self):
    return list(self.track)

  def updateTrack(self, value):
    self.track.update(value)


class RealtimeGPSTrackEnv(object):
  """
  A RealtimeGPSTrackEnv is an object representing the true
  state of the bus system at a certain point in time, as
  told by GPS tracking devices.

  In future implementations this may include something like
  Kalman filtering on the tracking data in order to better
  estimate a vehicle's truly "current" position.
  
  For now it simply takes the last known position as the
  current one.
  """

  def __init__(self,**kwargs):
    pass

  def update(self):
    pass



class RealtimeSimulation(object):
  """
  The central operating class of the RealtimeSim module.
  Calling run() on a RealtimeSimulation object will eternally
  keep track of the current locations of both tracked and
  scheduled vehicles alike, reporting actual arrivals as they
  occur and their relation to the schedule.
  """
  
  def __init__(self,**kwargs):
    pass

  def run(self):
    
    self.initRealtimeEnvs()
    
    while True:
      
      self.updateRealtimeEnvs()
      
      
