import socket
import asyncore
from os import sys

import RealtimeSim

class RDConnHandler(asyncore.dispatcher):
  """

  """
  
  def __init__(self,sock,parent):
    asyncore.dispatcher.__init__(self,sock);
    self.parent = parent
    self.xml = ""

  def writable(self):
    return 0

  def redable(self):
    return 1

  def handle_connect(self):
    print "Connected"

  def handle_close(self):
    print "Closed"

  def handle_read(self):
    data = self.recv(5096)
    if len(data) == 0:
      print "XML data received"
      self.parent.data_received(self.xml)
      self.close()
    else:
      self.xml += data


class RealtimeDaemon(asyncore.dispatcher):
  """
  
  """

  def __init__(self,port):
    asyncore.dispatcher.__init__(self)
    print "Port:",port
    self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
    self.bind(('',port))
    self.listen(5)

    self.rtsim = RealtimeSim.RealtimeSimulation();


  def handle_accept(self):
    client,addr = self.accept()
    print "accepted connection from",addr
    return RDConnHandler(client,self)

  def handle_close(self):
    print "Daemon closed."

  def data_received(self,data):
    result = self.rtsim.updateVehicles(xml=data)
    if result:
      print result
      ((trip_id, offset, error), segment_id) = result
      gpssched = GPSBusTrack.GPSBusSchedule( segment_id = segment_id,
                                             trip_id = trip_id,
                                             offset = offset );
      db.export_lateness_data( gpssched, error )
      print "GTFS Matchup Discovered"
      print "Trip:",trip_id
      for actual_arrival in gpssched.getGPSSchedule():
        print "  Arrived at stop %s at time %s, which was %s seconds late" \
            % (actual_arrival['stop_id'], 
               actual_arrival['actual_arrival_time_seconds'],
               actual_arrival['actual_arrival_time_seconds']
               - actual_arrival['departure_time_seconds'])



if __name__ == "__main__":
  import time
  rd = RealtimeDaemon(5050 + (int(time.time())%60) );
  asyncore.loop()

