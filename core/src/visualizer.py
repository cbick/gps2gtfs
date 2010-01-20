import pygame
import math
import time


class OSMManager(object):
  """
  An OSMManager manages the retrieval and storage of Open Street Map
  images. The basic utility is the createOSMImage() method which
  automatically gets all the images needed, and tiles them together 
  into one big image.
  """
  def __init__(self):
    pass

  def getTileCoord(self, lon_deg, lat_deg, zoom=14):
    """
    Given lon,lat coords in DEGREES, and a zoom level,
    returns the (x,y) coordinate of the corresponding tile #.
    (http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Python)
    """
    lat_rad = lat_deg * math.pi / 180.0
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + 
                                (1 / math.cos(lat_rad))) 
                 / math.pi) / 2.0 * n)
    return(xtile, ytile)

  def getTileURL(self, tile_coord, zoom=14):
    """
    Given x,y coord of the tile to download, and the zoom level,
    returns the URL from which to download the image.
    """
    params = (zoom,tile_coord[0],tile_coord[1])
    return "http://tile.openstreetmap.org/%d/%d/%d.png" % params

  def getLocalTileFilename(self, tile_coord, zoom=14):
    """
    Given x,y coord of the tile, and the zoom level,
    returns the filename to which the file would be saved
    if it was downloaded. That way we don't have to kill
    the osm server every time the thing runs.
    """
    params = (zoom,tile_coord[0],tile_coord[1]);
    return "maptiles/%d_%d_%d.png" % params

  def retrieveTileImage(self,tile_coord,zoom=14):
    """
    Given x,y coord of the tile, and the zoom level,
    retrieves the file to disk if necessary and 
    returns the local filename.
    """
    import urllib
    import os.path as path
    filename = self.getLocalTileFilename(tile_coord,zoom)
    if not path.isfile(filename):
      url = self.getTileURL(tile_coord,zoom)
      urllib.urlretrieve(url, filename=filename);
    return filename

  def tileNWLatlon(self,tile_coord,zoom=14):
    """
    Given x,y coord of the tile, and the zoom level,
    returns the (lat,lon) coordinates of the upper
    left corner of the tile.
    """
    xtile,ytile = tile_coord
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = lat_rad * 180.0 / math.pi
    return(lat_deg, lon_deg)


  def createOSMImage(self, minlon, maxlon, minlat, maxlat,zoom=14):
    """
    Given bounding latlons (in degrees), and an OSM zoom level,
    creates a pygame image constructed from OSM tiles.
    Returns (img,bounds) where img is the constructed pygame image,
    and bounds is the (lonmin,lonmax,latmin,latmax) bounding box
    which the tiles cover.
    """
    topleft = minX, minY = self.getTileCoord(minlon, maxlat);
    bottomright = maxX, maxY = self.getTileCoord(maxlon, minlat);
    new_maxlat, new_minlon = self.tileNWLatlon( topleft, zoom )
    new_minlat, new_maxlon = self.tileNWLatlon( (maxX+1,maxY+1), zoom )
    # tiles are 256x256
    pix_width = (maxX-minX+1)*256
    pix_height = (maxY-minY+1)*256
    surf = pygame.Surface( (pix_width,pix_height) )
    print "Retrieving %d tiles..." % ( (1+maxX-minX)*(1+maxY-minY) ,)

    for x in range(minX,maxX+1):
      for y in range(minY,maxY+1):
        fname = self.retrieveTileImage((x,y),zoom)
        img = pygame.image.load(fname);
        x_off = 256*(x-minX)
        y_off = 256*(y-minY)
        surf.blit( img, (x_off,y_off) );
        del img
    print "... done."
    return surf, (new_minlon, new_maxlon, new_minlat, new_maxlat)




class SimViz(object):
  """
  A class which knows how and when to display itself on a surface
  inside of a Simulation.
  """
  
  def drawToSurface(self,simtime,surf,getXY):
    """
    Draws this viz on the supplied surface.
    This should be implemented by subclasses.
    """
    raise Exception, "UNIMPLEMENTED"



class BusStopViz(SimViz):
  """Draws a small square at a bus stop location"""
  def __init__(self,location,label,color,width=5):
    self.label = label;
    self.loc = location;
    self.color = color;
    self.width = width

  def drawToSurface(self,simtime,surf,getXY):
    x,y = getXY(self.loc[0],self.loc[1]);
    width=self.width
    surf.fill(self.color,pygame.Rect(x-width/2,y-width/2,width,width));

class BusArrivalViz(SimViz):
  """Draws a circle around a bus when it arrives at a stop"""
  def __init__(self,matchup,color,width=3,diameter=20,duration=10):
    """matchup should be a GPSBusSchedule object"""
    self.matchup = matchup
    self.color = color
    self.width = width
    self.duration = duration
    self.diam = diameter

  def drawToSurface(self,simtime,surf,getXY):
    arrived=False
    bt = self.matchup.bustrack
    for s in self.matchup.arrival_schedule:
      arrivetime=s['actual_arrival_time_seconds']
      if arrivetime is None: continue;
      if abs(arrivetime-simtime) <= self.duration:
        arrived=True
        ll = bt.getLocationAtTime(simtime);
        if ll is None:
          if (arrivetime < bt.min_time or arrivetime > bt.max_time):
            print "WARNING: Bus arrived when it doesn't exist"
        
        else:
          pygame.draw.circle(surf,self.color,getXY(*ll),
                             self.diam/2,self.width);
      elif arrived: #we stopped arriving places
        break

class BusMatchupViz(SimViz):
  """Draws a line between two bustracks whenever they both exist"""
  def __init__(self,bt1,bt2,color,width=3):
    self.bt1 = bt1;
    self.bt2 = bt2;
    self.color = color;
    self.width=width

  def drawToSurface(self,simtime,surf,getXY):
    t1,t2,c = self.bt1,self.bt2,self.color
    ll1=t1.getLocationAtTime(simtime)
    if ll1 is None: return
    ll2 = t2.getLocationAtTime(simtime)
    if ll2 is None: return
    x1,y1=getXY(*ll1)
    x2,y2=getXY(*ll2)
    pygame.draw.line(surf,c,(x1,y1),(x2,y2),self.width);


class BusTrackViz(object):
  """
  A transparent wrapper around a BusTrack object. Easy way to specify 
  a label and an image to display.
  """
  def __init__(self,bustrack,label,image):
    """
    Given bustrack a BusTrack object, label a string, and image a
    filename, creates a BusTrackViz wrapper around bustrack with
    the given label and image for visualization.
    """
    self.track = bustrack;
    self.label = label;
    self.image = pygame.image.load(image);

  def __eq__(self,other):
    return (self.track == other.track);

  def __hash__(self):
    return hash(self.track)

  def __getattr__(self,attr):
    """This does the wrapping around the bustrack"""
    return self.track.__getattribute__(attr);


## !FIXME! for past-midnight error
class Simulation(object):
  """
  A collection of BusTrackViz's and a timer, of sorts. This lets the 
  visualizer say "Give me coordinates of each bus at time T". A run()
  method is provided which displays the simulation in a pygame window.
  """
  
  def __init__(self, bustrackvizs, simvizs, initTime = 0):
    """
    Given a set of BusTrackViz objects and a list of generiv SimViz objects, 
    and optionally an initial time, creates a Simulation object.
    """
    self.tracks = bustrackvizs;
    self.other_vizs = simvizs;
    self.__findBoundingBox();
    self.__findTimeWindow();
    #self.__sortTracks();

    self.time = 10000
    self.setTime(initTime);

  def __findBoundingBox(self):
    """Finds the latlon box bounding all objects"""
    init_box = (1e6,-1e6,1e6,-1e6);
    def helper(left,right):
      right = right.getBoundingBox();
      return (min(left[0],right[0]),
              max(left[1],right[1]),
              min(left[2],right[2]),
              max(left[3],right[3]));
    self.bounding_box = reduce( helper, self.tracks, init_box );

  def __findTimeWindow(self):
    """Finds the min and max times over all routes"""
    init_window = (1e6,-1e6);
    def helper(left,right):
      right = right.getRouteTimeInterval();
      return (min(left[0],right[0]),
              max(left[1],right[1]));
    self.time_window = reduce( helper, self.tracks, init_window );


  def __sortTracks(self):
    """Sorts tracked objects in order of increasing start time"""
    def tcmp(t1,t2):
      return cmp(t1.getRouteTimeInterval()[0],
                 t2.getRouteTimeInterval()[0]);
    self.tracks.sort(cmp=tcmp);

  def setTime(self,time):
    """
    Moves all bus tracks to the given time.
    """
    if time < self.time:
      for t in self.tracks: t.getLocationAtTime(time);
    self.time = min( max(time, self.time_window[0] ), self.time_window[1] );
    # Sets all the tracks to the correct location

  def printTime(self):
    hours = int(self.time/3600)
    minutes = int( (self.time % 3600) / 60 )
    seconds = int( (self.time % 60) )
    print "%02d:%02d:%02d" % (hours,minutes,seconds)

  def getXY(self,lat,lon,bounds,ssize):
    """
    Given coordinates in lon,lat, and a screen size,
    returns the corresponding (x,y) pixel coordinates.
    """
    x_ratio = ( (lon - bounds[0]) /
                (bounds[1]-bounds[0]) )
    y_ratio = 1.0 - ( (lat - bounds[2]) / 
                      (bounds[3]-bounds[2]) )
    x,y = int(x_ratio*ssize[0]), int(y_ratio*ssize[1])
    return x,y

  def run(self, speed=0.0, windowsize=(1280,800), refresh_rate = 1.0):
    """
    Pops up a window and displays the simulation on it.
    Speed is advancement of sim in seconds/second.
    Refresh rate is pause in seconds between frames.
    Windowsize is the desired (width,height) of the display window.
    """
    pygame.init()
    green = pygame.Color(80,255,80);
    black = pygame.Color(0,0,0);
    notec = pygame.Color(200,200,80);
    fnt = pygame.font.Font("/Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/site-packages/pygame/freesansbold.ttf",10);
    

    osm = OSMManager();
    bg_big, new_bounds = osm.createOSMImage(*self.bounding_box);
    w_h_ratio = float(bg_big.get_width()) / bg_big.get_height();
    # Make the window smaller to keep proportions
    newwidth = int(windowsize[1]*w_h_ratio)
    newheight= int(windowsize[0]/w_h_ratio)
    if newwidth > windowsize[0]:
      windowsize = windowsize[0],newheight
    elif newheight > windowsize[1]:
      windowsize = newwidth, windowsize[1]

    screen = pygame.display.set_mode(windowsize);

    bg_small = pygame.transform.smoothscale(bg_big,windowsize);
    del bg_big;

    lastTime = self.time;
    getXY = lambda lat,lon: self.getXY(lat,lon,new_bounds,windowsize);

    exit = False
    while not exit:
      for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
          exit = True
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
          speed = max( (speed + 1) * 1.4 , (speed / 1.4) + 1 )
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
          speed = min( (speed / 1.4) - 1 , (speed - 1) * 1.4 )
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
          speed = 0.0
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
          self.time = self.time_window[0];
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
          self.time = self.time_window[1];
      mousex,mousey = pygame.mouse.get_pos();
      selected=None;
          
      if self.time != lastTime:
        self.printTime();

      lastTime = self.time;


      ## Draw the background
      screen.blit(bg_small, (0,0));


      ## Draw the tracked objects

      # track viz's
      for t in self.tracks:
        ll = t.getLocationAtTime(self.time);
        if ll is None:
          continue
        lat,lon = ll
        x,y = getXY(lat,lon)
        img = t.image;
        w,h=img.get_rect().width,img.get_rect().height
        if abs(x-mousex)<w/2 and abs(y-mousey)<h/2:
          selected=t
        x = x - w/2
        y = y - h/2

        screen.blit(img, (x,y))
       
      # generic viz's
      for sviz in self.other_vizs:
        sviz.drawToSurface(self.time,screen,getXY);        
      

      if selected:
        #pygame.draw.rect(screen,notec,pygame.Rect(mousex,mousey,200,80));
        text = fnt.render(selected.label, True,black,notec)
        screen.blit(text, (mousex,mousey-10))
        del text
        
      pygame.display.flip()

      time.sleep(refresh_rate);
      self.setTime(self.time + speed*refresh_rate);
      
    del bg_small
    pygame.display.quit()


def test_GTFS(tids=range(2912979-9,2912979+1)):
  import GTFSBusTrack as tracker
  import sys
  btvs=[]
  print "Loading GTFS data for %d routes..." % (len(tids),)
  ix=0
  for tid in tids:
    ix+=1
    bt = tracker.GTFSBusTrack(tid);
    btv = BusTrackViz(bt,'test',"images/bus_small.png");
    if bt.__dict__.get('interpolation') is not None:
      btvs.append(btv);
      print "+",ix
    else:
      print "-",ix
    sys.stdout.flush()
  print "...done. Begining simulation..."
  sim = Simulation(btvs);
  sim.run(speed=0,refresh_rate=0.02);


def test_GPS(route_short_name,rte=None,num=None):
  import GPSBusTrack as gps
  import GTFSBusTrack as gtfs
  if rte is None:
    rte = gps.Route(route_short_name);
  segs = [s for s in rte.segments(True)];
  btsegs=[]

  for i,seg in enumerate(segs):
    if num and i>=num: break
    bt = gps.GPSBusTrack(seg);
    btv = BusTrackViz(bt,'test',"images/bus_small.png");
    gtfs_trip_id,offset,error=bt.getMatchingGTFSTripID()
    bt2 = gtfs.GTFSBusTrack(gtfs_trip_id);
    print "BEST MATCHING TRIP ID: %s (error: %d)"%(bt2.trip_id,error)
    btv2 = BusTrackViz(bt2,'test',"images/bus.png");
    btsegs.extend([btv,btv2]);
  sim = Simulation(btsegs)
  sim.run(speed=0,refresh_rate=0.1);


def test_matched_GPS(segment_ids):
  import GPSBusTrack as gps
  gtfs_tracks = {}
  gps_tracks = []
  vizs = []
  stops = set()
  for i,segid in enumerate(segment_ids):
    print "Loading segment %s (%d/%d)..." %(segid,i+1,len(segment_ids))
    bus = gps.GPSBusSchedule(segid);
    gps_track = bus.getGPSBusTrack();
    gtfs_schedule = bus.getGTFSSchedule();
    service_id = gtfs_schedule.service_id;

    viz1 = BusTrackViz(gps_track,'tracked:'+str(segid),
                       "images/bus_small.png");
    
    gps_tracks.append(viz1);

    gtfs_key = (gtfs_schedule.trip_id,gtfs_schedule.offset)
    if not gtfs_tracks.has_key( gtfs_key ):
      gtfs_track = bus.getGTFSBusTrack();
      viz2 = BusTrackViz(gtfs_track,'scheduled:'+str(gtfs_track.trip_id),
                         "images/bus.png");
      gtfs_tracks[gtfs_key] = viz2
    else:
      viz2 = gtfs_tracks[gtfs_key]

    mviz = BusMatchupViz(viz1,viz2,service_colors[service_id]);
    arriv_viz = BusArrivalViz(bus,service_colors[service_id],duration=5);
    for stop in bus.getGPSSchedule():
      stops.add( (stop['stop_lat'],stop['stop_lon']) )
    vizs.append(mviz);
    vizs.append(arriv_viz);

    print "ok"

  print "Loading stops..."
  for stop in stops:
    vizs.append(BusStopViz(stop,'asdf',pygame.Color(0,0,0),5))
  print "ok"
  sim = Simulation(gtfs_tracks.values()+gps_tracks,vizs);
  sim.run(speed=0,refresh_rate=0.1);

service_colors = {
  '1':pygame.Color(255,80,80),
  '2':pygame.Color(80,255,80),
  '3':pygame.Color(80,80,255)
}

if __name__ == "__main__":
  import dbutils as db
  #test_tids = db.get_all_trip_ids_for_times('1','20000','21000');
  #test_tids = db.get_all_trip_ids_for_times('1','24000','30000');
  #test_GTFS(test_tids)
  #test_GPS('18',num=None);
  cur = db.get_cursor();
  cur.execute("""select gps_segment_id from gps_segments tr 
                   inner join gtf_trips gt on gt.trip_id=tr.trip_id 
                   inner join gtf_routes gr on gt.route_id = gr.route_id
                   inner join gtf_trip_information gti on gti.trip_id=gt.trip_id
                 where gr.route_short_name in ('19','10')
                   and 27000 <= first_arrival and first_arrival <= 29000
              """
              );
  segids = [r['gps_segment_id'] for r in cur];
  cur.close();
  test_matched_GPS(segids);
  #test_matched_GPS(map(lambda i:str(i+1), range(500)))
  #test_matched_GPS(("35",))
  #test_matched_GPS(("1","2"))


