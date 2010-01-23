# Copyright (c) 2010 Colin Bick, Robert Damphousse

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from os import sys,path

mydir = path.abspath(path.dirname(sys.argv[0]))
dbdir = mydir+"/../../common/src/"
sys.path.append(dbdir)

from dbutils import SQLExec, get_cursor, SDHandler, commit
import datetime

def get_all_trip_ids():
  cur = get_cursor()
  SQLExec(cur,"select trip_id from gtf_trips")
  ret = [r['trip_id'] for r in cur]
  cur.close()
  return ret

def update_routes(vehicle_data):
  """
  Inserts GPS tracking data into the database.
  Vehicle data is a list of dicts mapping attributes to values.
  Attributes can be the following:

    id -- the vehicle id (string)
    routeTag -- the route id (string)
    dirTag -- identifier for the route direction (string)
    lat -- latitude of the vehicle (float)
    lon -- longitude of the vehicle (float)
    secsSinceReport -- how old the data was upon recording time (integer)
    predictable -- i have no idea what this field means, ask nextbus (string)
    heading -- the direction the bus is moving (integer -- degrees?)
    update_time -- the recording time (when this data was retrieved) (timestamp)

  Of the above, update_time and secsSinceReport are required. If you
  don't have any value for secsSinceReport then put in a 0. If you don't
  have any value for update_time then what exactly are you trying to
  accomplish?
  """
  if len(vehicle_data) == 0:
    print "empty list"
    return

  query_start = "insert into vehicle_track (" \
      + ",".join(vehicle_data[0].keys()) + ", reported_update_time) values (" \
      + ",".join(map(lambda attr: "%(" + attr + ")s",vehicle_data[0].keys())) \
      + ","

  query_end = ")"

  cur = get_cursor();
  for vdata in vehicle_data:
    q = ("date_trunc('second',TIMESTAMP '%(update_time)s') - " \
        + "interval '%(secsSinceReport)s seconds'") \
        % vdata
    q = query_start + q + query_end
    #print q
    SQLExec(cur,q,vdata);
  cur.close();
  


def getGTFSRouteData(route_id):
  """
  Given a route ID, returns a row from the GTFS table as a dict-like type.
  Keys:
  'route_long_name',
  'route_type',
  'route_text_color',
  'route_color',
  'agency_id',
  'route_id',
  'route_url',
  'route_desc',
  'route_short_name'
  """
  cur = get_cursor();
  SQLExec(cur,"select * from gtf_routes where route_id=%(id)s",{'id':str(route_id)});
  ret = cur.next();
  cur.close();
  return ret;


def getGTFSTripData(trip_id):
  """
  Given a trip ID, returns (trip_header, trip, shape),
  where trip_header is a row from the GTFS table,
  Keys:
  'block_id',
  'route_id',
  'direction_id',
  'trip_headsign',
  'shape_id',
  'service_id',
  'trip_id',
  'trip_short_name'

  trip is a list of rows holding info about each stop along the route
  (The order of the rows in trip is the order of the stops along the route),
  Keys:
  'stop_sequence',
  'parent_station',
  'trip_id',
  'pickup_type',
  'stop_headsign',
  'arrival_time_seconds',
  'stop_name',
  'departure_time_seconds',
  'stop_timezone',
  'timepoint',
  'arrival_time',
  'stop_url',
  'stop_id',
  'stop_desc',
  'location_type',
  'departure_time',
  'stop_code',
  'stop_lat',
  'zone_id',
  'stop_lon',
  'shape_dist_traveled',
  'drop_off_type'

  and shape is a list of rows holding info about the geometry traversed by
  the route.
  Keys:
  'shape_pt_lat',
  'shape_id',
  'shape_pt_lon',
  'shape_pt_sequence',
  'shape_dist_traveled'
  """
  cur = get_cursor();
  if not isinstance(trip_id,basestring):
    trip_id = str(trip_id);

  SQLExec(cur,"select * from gtf_trips where trip_id=%(id)s",
          {'id':trip_id});
  trip_header = cur.next();

  SQLExec(cur,
          "select * from gtf_stop_times natural join gtf_stops \
              where trip_id=%(id)s order by stop_sequence",
          {'id':trip_id});
  stops = [row for row in cur];

  SQLExec(cur,
          "select * from gtf_shapes where shape_id = %(id)s \
              order by shape_pt_sequence",
          {'id':trip_header['shape_id']});
  shape = [row for row in cur];
  
  cur.close();
  return (trip_header, stops, shape);




def get_route_for_dirtag(dirtag):
  """
  Given a nextbus dirtag, returns the GTFS route ID
  """
  cur = get_cursor();
  SQLExec(cur,
          """Select route_id from routeid_dirtag where dirtag=%(dirtag)s""",
          {'dirtag':dirtag});
  ret = [r[0] for r in cur];
  cur.close()

  if len(ret) > 1:
    print "MORE THAN ONE ROUTE PER DIRTAG"
    print "  dirtag:",dirtag
    print "  routes:",ret
  return ret[0]

def get_direction_for_dirtag(dirtag):
  """
  Given a nextbus dirtag, returns the GTFS direction ID
  """
  dir = dirtag.find("OB");
  if dir < 0: dir = "Inbound"
  else: dir = "Outbound"

  cur = get_cursor();
  SQLExec(cur,
          """Select direction_id from gtfs_directions 
               where description=%(dir)s""",
          {'dir':dir});
  ret = cur.next()[0];
  
  cur.close();
  return ret;

def get_route_dirtags(route_short_name):
  """
  Given the short name for a route, returns a list of dirtags
  which are associated with that route.
  """
  cur = get_cursor();
  SQLExec(cur,
          """SELECT dirtag FROM routeid_dirtag
               WHERE route_id IN (select route_id from gtf_routes 
                                    where route_short_name = %(rsn)s)""",
               {'rsn':route_short_name});
  ret = map(lambda r: r[0], cur);

  cur.close()
  return ret;


def get_vehicle_reports(dirtags):
  """
  Given a list of dirtags, returns a list of dictlike rows of 
  vehicle tracking reports, sorted in ascending order of update time.
  Keys:
  'id',
  'lat',
  'lon',
  'routetag',
  'dirtag',
  'reported_update_time'
  """
  if len(dirtags) == 0:
    return []
  p = {}
  for i,d in enumerate(dirtags):
    p['k'+str(i)] = d;
  sql = """SELECT id,lat,lon,routetag,dirtag,reported_update_time 
             from vehicle_track 
             where dirtag IN ( %s )
           order by reported_update_time asc""" \
      % (','.join(map(lambda k: "%("+k+")s", p.keys())) ,)

  cur = get_cursor();
  print "Executing..."
  SQLExec(cur, sql, p);
  print "Retrieving..."
  ret = cur.fetchall();
  print "...done."

  cur.close();
  return ret;


def get_shapes_for_route(route_short_name):
  """
  Given a route short name, returns a list of dictlike rows
  containing the shapes associated with that route, sorted in
  order of ascending shape ID then ascending shape point sequence.
  Keys:
  'shape_id',
  'shape_pt_lat',
  'shape_pt_lon',
  'shape_pt_sequence',
  'shape_dist_traveled',
  'dirtag'
  """
  cur = get_cursor();
  SQLExec(cur, """SELECT gtf_shapes.*,shape_dirtag.dirtag 
                    FROM gtf_shapes,shape_dirtag
                    WHERE gtf_shapes.shape_id = shape_dirtag.shape_id 
                      and gtf_shapes.shape_id IN 
                        (select distinct(shape_id) from gtf_trips 
                           where route_id IN
                             (select route_id from gtf_routes 
                                where route_short_name = %(route_short_name)s
                             )
                        )
                    ORDER BY gtf_shapes.shape_id asc, 
                             gtf_shapes.shape_pt_sequence asc""",
          {'route_short_name':route_short_name});
  ret = [r for r in cur];

  cur.close();
  return ret;



def get_serviceIDs_for_date(date):
  """
  Given a datetime.date object, returns a list of GTFS service ID's
  active for that date.
  """
  global SDHandler
  return SDHandler.effective_service_ids(date);


def get_previous_trip_ID(trip_id, start_date, offset, numtrips=10):
  """
  Given GTFS trip ID, the date it ran on, and the schedule's offset in seconds,
  finds the immediately previous GTFS trip ID with the same direction and 
  route. The start_date is necessary in cases close to midnight.
  """
  
  cur = get_cursor();

  SQLExec(cur,"select route_id,direction_id from gtf_trips where trip_id=%(tid)s",
          {'tid':trip_id});
  routeinfo = list(cur)[0];
  route_id,dir_id = map(lambda s:routeinfo[s], 
                        "route_id,direction_id".split(","));
  
  SQLExec(cur,"""select min_depart as mintime
                   from gtf_trip_start_times where trip_id=%(tid)s""",
          {'tid':trip_id});

  # start_time is the time the bus started for the date start_date
  start_time = list(cur)[0]['mintime'] - offset;


  yesterday_ids = map(lambda sid: "'"+str(sid)+"'",
                      get_serviceIDs_for_date(start_date - 
                                              datetime.timedelta(days=1)));
  today_ids = map(lambda sid: "'"+str(sid)+"'", 
                  get_serviceIDs_for_date(start_date));
  sql = """(select trip_id, 0 as offset,
                  abs(min_depart-%(start_time)s) as diff 
             from gtf_trips natural join gtf_trip_start_times
             where direction_id=%(dir_id)s and route_id=%(route_id)s
               and service_id in (""" + ','.join(today_ids) + """)
               and min_depart < %(start_time)s
           union
           select trip_id, 86400 as offset,
                 abs(min_depart-86400-%(start_time)s) as diff
             from gtf_trips natural join gtf_trip_start_times
             where direction_id=%(dir_id)s and route_id=%(route_id)s
               and service_id in (""" + ','.join(yesterday_ids) + """)
               and min_depart-86400 < %(start_time)s
           ) order by diff limit """ + str(numtrips)

  SQLExec(cur,sql,
          {'start_time':start_time,'dir_id':dir_id,'route_id':route_id});
  
  ret = [(r['trip_id'],r['offset']) for r in cur]

  cur.close()

  if len(ret) == 0:
    return None
  return ret


def get_best_matching_trip_ID(route_id, dir_id, start_date, start_time, 
                              num_results=1):
  """
  Given GTFS route and direction IDs, a datetime.date object representing
  the day of the route, and start_time an integer representing the begin 
  time of the route as seconds into the day, returns a list of the
  num_results best matching GTFS trips, in order of best matching start
  datetime.
  Each item in the list is of the form:
    (trip_id, offset_seconds)
  where trip_id is the GTFS trip ID, and offset_seconds represents the
  offset (in seconds) that need be applied to the trip for any times 
  in the format of "seconds into day." This is necessary because
  sometimes the best matching trip will come from the previous day's
  service schedule, and so you will need to subtract 1 day = 86400 seconds
  from the times for that bus.

  For example, a bus running at 3am might be from today's schedule at
  03:00, or it might be from yesterday's schedule at 27:00. If a match
  is found for 03:00 today, then the offset returned is 0. If a match
  is found for 27:00 yesterday, then the offset returned is 86400.
  """
  yesterday_ids = map(lambda sid: "'"+str(sid)+"'",
                      get_serviceIDs_for_date(start_date - 
                                               datetime.timedelta(days=1)));
  print "  Yesterday's IDs:",yesterday_ids

  today_ids = map(lambda sid: "'"+str(sid)+"'", 
                    get_serviceIDs_for_date(start_date));
  print "  Today's IDs:",today_ids

  tomorrow_ids = map(lambda sid: "'"+str(sid)+"'",
                     get_serviceIDs_for_date(start_date +
                                              datetime.timedelta(days=1)));
  print "  Tomorrow's IDs:",tomorrow_ids

  sql = """(select trip_id, 0 as offset,
                  abs(min_depart-%(start_time)s) as diff 
             from gtf_trips natural join gtf_trip_start_times
             where direction_id=%(dir_id)s and route_id=%(route_id)s
               and service_id in (""" + ','.join(today_ids) + """)
           union
           select trip_id, 86400 as offset,
                 abs(min_depart-86400-%(start_time)s) as diff
             from gtf_trips natural join gtf_trip_start_times
             where direction_id=%(dir_id)s and route_id=%(route_id)s
               and service_id in (""" + ','.join(yesterday_ids) + """)
           union
           select trip_id, -86400 as offset,
                 abs(min_depart+86400-%(start_time)s) as diff
             from gtf_trips natural join gtf_trip_start_times
             where direction_id=%(dir_id)s and route_id=%(route_id)s
               and service_id in (""" + ','.join(tomorrow_ids) + """)
           ) order by diff limit """ + str(num_results)

  cur = get_cursor()
  SQLExec(cur,sql,
          {'start_time':start_time,'dir_id':dir_id,'route_id':route_id});
  
  ret = [(r['trip_id'],r['offset']) for r in cur]
  if len(ret) == 0:
    ret = None

  cur.close()
  return ret


def getMaxSegID():
  """
  Returns the largest vehicle segment ID found in the "tracked_routes"
  table (see the export_gps_route function below). This can be used to
  construct a unique ID for further segments.

  Note that there should be a 1-1 correspondence between segment and
  trip IDs for any particular service day. Of course part of the point
  of this is to eliminate any cases where this is not true in a meaningful
  way.
  """
  sql = """select max(gps_segment_id) from gps_segments"""
  cur = get_cursor()
  SQLExec(cur,sql);
  ret = [r['max'] for r in cur];
  cur.close();

  if ret[0] is None:
    return 0;
  return ret[0];


  

def export_gps_route( trip_id, trip_date, segment_id, vehicle_id, 
                      gtfs_error, offset_seconds,
                      gps_data, segment_exists = False):
  """
  Writes the given entry to the "tracked_routes" table. This table is used
  to cache the results of finding and filtering only the valid routes as
  represented in the GPS dataset.
  
  trip_id: the GTFS trip id
  trip_date: the date of the trip
  segment_id: unique identifier for this GPS segment (see getMaxSegID())
  vehicle_id: as reported in the GPS data
  gtfs_error: The distance from the matched GTFS trip as measured by
              the GPSBusTrack metric
  offset_seconds: Number of seconds to subtract from GTFS trip to normalize.

  gps_data: A list of (lat, lon, reported_update_time) values, exactly as
            reported in the GPS dat. Note that reported_update_time should
            be a timestamp.

  WARNING: No effort is made to prevent duplicate entries! If you do this
  more than once for the same route then YOU MUST DELETE IT FIRST!
  """

  sql1 = """insert into gps_segments (
              gps_segment_id, trip_id, trip_date, vehicle_id,
              schedule_error, schedule_offset_seconds
         ) VALUES (
               %(seg_id)s,%(trip_id)s,%(trip_date)s,%(vehicle_id)s,
               %(gtfs_error)s, %(offset)s
         )"""

  sql2 = """insert into tracked_routes (
               gps_segment_id, lat, lon, reported_update_time
             ) VALUES (
               %(seg_id)s,%(lat)s,%(lon)s,%(reported_update_time)s
             )"""
  cur = get_cursor()

  if not segment_exists:
    SQLExec(cur,sql1,
            {'trip_id':trip_id,'trip_date':trip_date,'vehicle_id':vehicle_id,
             'gtfs_error':str(gtfs_error),'seg_id':str(segment_id),
             'offset':offset_seconds});
  
  for lat,lon,reported_update_time in gps_data:
    SQLExec(cur,sql2,
            {'lat':lat,'lon':lon,
             'reported_update_time':reported_update_time,
             'seg_id':str(segment_id)});

  cur.close()


def load_gps_segment_header(segment_id):
  """
  Given a segment ID, returns:
     (trip_id,trip_date,vehicle_id,schedule_error,offset)
  where trip_id is the gtfs trip ID, trip_date is the date on whose schedule
  the trip took place, vehicle_id is the gps vehicle's ID, schedule_error
  is the measured error between the GPS route and the GTFS schedule, and 
  offset is the number of seconds to substract from any GTFS schedule times.
  """
  sql_header = """select trip_id, trip_date, vehicle_id, schedule_error,
                    schedule_offset_seconds
                  from gps_segments
                  where gps_segment_id=%(segID)s"""

  cur = get_cursor()
  SQLExec(cur,sql_header,{'segID':segment_id});
  header = [r for r in cur][0];
  cur.close()

  trip_id,trip_date,veh_id,sched_err,sched_off= \
      map(lambda c:header[c],
          ('trip_id','trip_date','vehicle_id','schedule_error',
           'schedule_offset_seconds'));
  return trip_id,trip_date,veh_id,sched_err,sched_off



def load_gps_route(segment_id):
  """
  Given a segment ID, loads the associated trip from the tracked_routes table
  in order of increasing report time. 

  Returns (trip_id, trip_date, vehicle_id, schedule_error, offset, route)
  where trip_id is the gtfs trip ID, trip_date is the date on whose schedule
  the trip took place, vehicle_id is the gps vehicle's ID, schedule_error
  is the measured error between the GPS route and the GTFS schedule, offset 
  is the number of seconds to substract from any GTFS schedule times, and
  route is a list of [lat,lon,reported_update_time] triples.
  """
  
  

  sql = """select lat, lon, reported_update_time
           from tracked_routes
           where gps_segment_id=%(segID)s
           order by reported_update_time"""

  cur = get_cursor()  
  SQLExec(cur,sql,{'segID':segment_id});
  res = [r for r in cur];
  cur.close();

  trip_id,trip_date,veh_id,sched_err,sched_off= load_gps_segment_header(segment_id);

  rows = [[r['lat'],r['lon'],r['reported_update_time']] for r in res];

  return trip_id,trip_date,veh_id,sched_err,sched_off,rows



def correct_gps_schedule( segment_id, trip_id, gtfs_error, offset_seconds,
                       gps_data ):
  sql1="""update gps_segments set trip_id=%(tid)s,schedule_error=%(gerr)s,
            schedule_offset_seconds=%(os)s
          where gps_segment_id=%(gid)s"""
  sql2="""delete from gps_stop_times where gps_segment_id=%(gid)s"""
  cur = get_cursor()
  SQLExec(cur,sql1,{'tid':trip_id,'gerr':gtfs_error,'os':offset_seconds,
                    'gid':segment_id});
  SQLExec(cur,sql2,{'gid':segment_id});
  cur.close()
  export_gps_schedule( segment_id, gps_data )


def export_gps_schedule(segment_id,schedule):
  """
  Given a gps segment ID and a list of dictlike rows having the keys:
    'stop_id', GTFS stop ID
    'stop_sequence', GTFS trip stop sequence
    'stop_headsign', 
    'pickup_type',
    'drop_off_type',
    'shape_dist_traveled',
    'timepoint',
    'arrival_time_seconds', time in seconds into day
    'departure_time_seconds', time in seconds into day
    'actual_arrival_time_seconds', actual arrival in seconds into day
    'actual_departure_time_seconds' actual departure in seconds into day
    'seconds_since_last_stop' time elapsed since arrival at previous stop
    
  exports the rows appropriately into the database.
  """

  keystr = \
         """stop_id,stop_sequence,stop_headsign,pickup_type,"""\
         """drop_off_type,shape_dist_traveled,timepoint,"""\
         """arrival_time_seconds,departure_time_seconds,"""\
         """actual_arrival_time_seconds,seconds_since_last_stop,"""\
         """prev_stop_id"""
  keys = keystr.split(",")
  
  sql = """insert into gps_stop_times (gps_segment_id,"""+keystr+""")

           values

           (%(gps_seg_id)s,""" \
            +",".join(map(lambda k: "%("+k+")s", keys)) + """)"""

  cur = get_cursor()
  for row in schedule:
    params = {}
    params['gps_seg_id']=segment_id
    for key in keys:
      params[key]=row[key]
    SQLExec(cur,sql,params);
  cur.close()


def load_gps_schedule(segment_id):
  """
  Given a segment_id, loads the corresponding arrival schedule from the
  gps_stop_times table in the database.

  Returns a list of dictlike rows, each with the following keys:
      'stop_id'
      'stop_sequence'
      'stop_headsign'
      'pickup_type'
      'drop_off_type',
      'shape_dist_traveled',
      'timepoint',
      'arrival_time_seconds',
      'departure_time_seconds',
      'actual_arrival_time_seconds'
      'seconds_since_last_stop'

  The rows will be in order of increasing stop sequence.
  """
  
  sql = """select * from gps_stop_times 
             where gps_segment_id=%(segid)s
             order by stop_sequence asc"""
  cur = get_cursor();
  SQLExec(cur,sql,{'segid':segment_id});
  ret = list(cur);
  cur.close();
  return ret;


def export_trip_information(trip_id,first_arrive,first_depart,
                         trip_length,trip_duration):
  """
  Given a GTFS trip ID, the time (in seconds) of its first arrival and
  departure, the length of the whole trip in meters, and the duration
  of the trip in seconds, pushes it to the database.
  """
  
  sql="""insert into gtf_trip_information (trip_id,first_arrival,
           first_departure,trip_length_meters,trip_duration_seconds)
         values
           (%(tid)s,%(farr)s,%(fdep)s,%(lenm)s,%(durs)s)"""
  cur = get_cursor()
  SQLExec(cur,sql,{'tid':trip_id,'farr':first_arrive,'fdep':first_depart,
                   'lenm':str(trip_length),'durs':trip_duration});
  cur.close()


def export_trip_stop_information(trip_id,stop_sequence,stop_number,
                                 prev_stop_distance,cumulative_distance,
                                 prev_stop_travel_time):
  """
  Given a GTFS trip ID and stop sequence number, the number of this stop 
  along the route, the distance from the previous stop to this stop in meters,
  the cumulative distance from the beginning of the trip to this stop in
  meters, and the time in seconds it takes (according to the schedule) to
  get to this stop from the previous stop, pushes it to the database.
  """
  
  sql="""insert into gtf_stoptimes_information (trip_id, stop_sequence,
           trip_stop_number,prev_stop_distance_meters,
           cumulative_distance_meters,travel_time_seconds)
         values
           (%(tid)s,%(seq)s,%(num)s,%(dist)s,%(cdist)s,%(time)s)"""
  cur = get_cursor()
  if prev_stop_distance is not None:
    prev_stop_distance = str(prev_stop_distance)
  SQLExec(cur,sql,{'tid':trip_id,'seq':stop_sequence,'num':stop_number,
                   'dist':prev_stop_distance,
                   'cdist':str(cumulative_distance),
                   'time':prev_stop_travel_time});
  cur.close()


def get_segment_IDs(scheduled_only=True):
  cur = get_cursor();
  if scheduled_only:
    sql = "select gps_segment_id from gps_segments where trip_id is not null"
  else:
    sql = "select gps_segment_id from gps_segments"
  SQLExec(cur,sql)
  seg_ids = [s['gps_segment_id'] for s in cur]
  cur.close()
  return seg_ids

def get_route_names():
  cur = get_cursor()
  SQLExec(cur,"select route_short_name from gtf_routes");
  ret = [s['route_short_name'] for s in cur]
  cur.close()
  return ret


def populate_routeid_dirtag(deletefirst=False):
  """
  Populates routeid_dirtag table with all distinct instances of 
  (routeid,dirtag) from the vehicle tracking data table joined with
  the gtfs routes table.
  If deletefirst is true, then the routeid_dirtag table is truncated
  first.
  """
  cur = get_cursor()
  if deletefirst:
    SQLExec(cur,"""truncate routeid_dirtag""")

  SQLExec(cur,"""
insert into routeid_dirtag
(select distinct route_id,dirtag from vehicle_track vt inner join gtf_routes gr
on vt.routetag = gr.route_short_name
where vt.dirtag != 'null' and vt.dirtag is not null)
""")

  cur.close()



