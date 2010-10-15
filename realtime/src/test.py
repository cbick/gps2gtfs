from os import sys
import asyncore
import socket

if len(sys.argv) != 3:
  print "Usage: %s port fname" % (sys.argv[0],)
  sys.exit(1)

fname = sys.argv[2]
port = int(sys.argv[1])


f = open(fname,'r')
xml = "".join(f.readlines())
f.close()


class Uploader(asyncore.dispatcher):
  def __init__(self,xml,port):
    asyncore.dispatcher.__init__(self,None)
    self.xml = xml
    self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
    self.connect(('localhost',port))

  def writable(self):
    return 1

  def readable(self):
    return 0

  def handle_connect(self):
    pass
    #print "Connected"
    
  def handle_close(self):
    pass
    #print "Closed."

  def handle_write(self):
    #print "Uploading..."
    
    bytes = self.send(self.xml)
    self.xml = self.xml[bytes:]
    if self.xml == "":
      #print "done."
      self.close()

ul = Uploader(xml,port)
asyncore.loop()
