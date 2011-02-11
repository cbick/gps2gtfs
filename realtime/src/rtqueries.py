from dbutils import SQLExec,get_cursor,commit




def create_observation_id( trip_id, stop_id, day_of_week, stop_sequence ):
  """
  Inserts an entry with new observed_stop_id into observation_attributes.
  Returns the new ID.
  """
  ## observed_stop_id is not necessarily unique, across service intervals
  cur = get_cursor()
  SQLExec(cur,"select max(observed_stop_id) from observation_attributes")
  r = list(cur)

  if len(r) == 0 or r[0][0] is None:
    newid = 0
  else:
    newid = r[0][0] + 1

  sql = """\
insert into observation_attributes
  (observed_stop_id, trip_id, stop_id, stop_sequence, day_of_week)
values
  ( %(osid)s, %(tid)s, %(sid)s, %(seq)s, %(dow)s )
"""

  SQLExec(cur, sql, {'osid':newid, 'tid':trip_id, 'sid':stop_id,
                     'seq':stop_sequence, 'dow':day_of_week})
  cur.close()

  return newid


def get_observation_stop_id( trip_id, stop_id, day_of_week, stop_sequence,
                             auto_create = True):
  sql="""\
select observed_stop_id
from observation_attributes oa
where oa.trip_id=%(tid)s
  and oa.stop_sequence=%(seq)s
  and oa.day_of_week=%(dow)s
"""

  cur = get_cursor()
  SQLExec(cur, sql, {'tid':trip_id,'seq':stop_sequence,'dow':day_of_week})
  
  rows = [r[0] for r in cur]

  if len(rows) == 0:
    if auto_create:
      ret = create_observation_id(trip_id,stop_id,day_of_week,stop_sequence)
    else:
      ret = None
  elif len(rows) > 1:
    raise Exception, "Redundant observation IDs"
  else:
    ret = rows[0]

  return ret


def create_observation_row( trip_id, stop_id, day_of_week, stop_sequence, 
                             lateness_minutes, initial_num_obs=1 ):
  obs_id = get_observation_stop_id(trip_id,stop_id,day_of_week,stop_sequence,
                                   auto_create = True)
  sql = """\
insert into simplified_lateness_observations 
  ( minutes_late, num_observations, observed_stop_id )
values
  ( %(minutes)s, %(init)s, %(obsid)s )
"""
  cur = get_cursor()
  SQLExec(cur, sql, {'minutes':lateness_minutes,'init':initial_num_obs,
                     'obsid':obs_id})
  cur.close()


def record_observations( gpssched ):
  """
  Given a GPSBusSchedule, records simplified lateness observations
  """
  trip_id = gpssched.getGTFSSchedule().trip_id
  dow = gpssched.getTrackedVehicleSegment().reports[0].dayOfWeek()

  for arrival in gpssched.getGPSSchedule():
    stop_id = arrival['stop_id']
    stop_sequence = arrival['stop_sequence']

    if arrival['actual_arrival_time_seconds'] is None:
      continue # don't store null lateness entries

    lateness_seconds = (arrival['actual_arrival_time_seconds']
                        - arrival['departure_time_seconds'])

    lateness_observed( trip_id, stop_id, dow, stop_sequence, lateness_seconds )
    

def lateness_observed( trip_id, stop_id, day_of_week, stop_sequence, 
                       lateness_seconds, auto_create=True ):
  """
  Increments the count for the indicated observation and returns True. 
  If the entry does not exist, will create the entry if auto_create is 
  True, otherwise returns False.
  """
  sql = """\
update simplified_lateness_observations
set num_observations = num_observations+1
where minutes_late=%(lateness)s
  and observed_stop_id=%(osid)s
"""
  osid = get_observation_stop_id( trip_id,stop_id,day_of_week,stop_sequence,
                                  auto_create = False )
  # round to the nearest minute
  ret = True
  if lateness_seconds is not None:
    lateness_minutes = int( (lateness_seconds/60.0) + 0.5 )
  else:
    lateness_minutes = None
  cur = get_cursor()
  SQLExec(cur,sql, {'osid':osid,'lateness':lateness_minutes})

  if cur.rowcount == 0:
    if auto_create:
      create_observation_row(trip_id,stop_id,day_of_week,stop_sequence,
                             lateness_minutes,initial_num_obs=1)
    else:
      ret = False
  elif cur.rowcount > 1:
    raise Exception, "Redundant rows in observations table"

  cur.close()
  return ret


def measure_prob_mass( trip_id, stop_id, day_of_week, stop_sequence, 
                       lateness_bounds ):
  sql = """\
select num_observations, minutes_late
from simplified_lateness_observations slo
  inner join observation_attributes oa
    on slo.observed_stop_id = oa.observed_stop_id
      and oa.trip_id=%(tid)s
      and oa.stop_sequence=%(seq)s
      and oa.day_of_week=%(dow)s
"""

  cur = get_cursor()
  SQLExec(cur, sql, {'tid':trip_id,'seq':stop_sequence,'dow':day_of_week})

  rows = map( lambda r: (r['num_observations'],r['minutes_late']),
              cur.fetchall() );
  
  cur.close()

  reducer = lambda l,r: l+r[0]
  total = reduce( reducer, rows, 0 )
  sums = [0] * len(lateness_bounds)

  for i,(min,max) in enumerate(lateness_bounds):
    sums[i] = reduce(reducer,
                     filter( lambda r: min<=r[1]<=max, rows ),
                     0)
  
  if total == 0:
    return None

  return map(lambda i: float(sums[i])/total, 
             range(len(lateness_bounds)))




def get_stops( min_lat, max_lat, min_lon, max_lon ):
  sql = """\
select * from gtf_stops 
where stop_lat >= %(min_lat)s
  and stop_lat <= %(max_lat)s
  and stop_lon >= %(min_lon)s
  and stop_lon <= %(max_lon)s
"""
  cur = get_cursor()
  SQLExec(cur,sql,{'min_lat':min_lat,
                   'max_lat':max_lat,
                   'min_lon':min_lon,
                   'max_lon':max_lon})
  rows = cur.fetchall()
  cur.close()
  return map(dict,rows)


def get_stop_info( stop_id, day_of_week ):

  ## SF hack here, for now.
  ## Need to define a way of handling the "day of week"
  ## problem in terms of service IDs.
  if 0 <= day_of_week <= 4:
    service_id = '1'
  elif day_of_week == 5:
    service_id = '2'
  elif day_of_week == 6:
    service_id = '3'
  else:
    raise Exception, "Not a day of week"

  sql = """\
select gst.*, gt.*, gr.*, oa.observed_stop_id 
from gtf_stop_times gst
  inner join gtf_trips gt on gst.trip_id = gt.trip_id
  inner join gtf_routes gr on gt.route_id = gr.route_id
  left outer join observation_attributes oa
    on oa.trip_id = gst.trip_id 
      and oa.stop_sequence = gst.stop_sequence
      and oa.day_of_week=%(dow)s
where gst.stop_id=%(stopid)s
  and gt.service_id=%(sid)s
order by gr.route_short_name, gst.arrival_time_seconds
"""

  cur = get_cursor()
  SQLExec(cur,sql,{'stopid':stop_id,'sid':service_id,'dow':day_of_week})
  rows = cur.fetchall()
  cur.close()

  return map(dict,rows)


def simplified_lateness_counts():
  """
  This is a one-time function to translate all data from datamining_table
  into simplified_lateness_observations.
  """
  sql = """
select dm.lateness, dm.gtfs_trip_id, dm.stop_id, dm.stop_sequence, 
  ((EXTRACT(DOW FROM gs.trip_date) + 6)::integer % 7) as dow
from datamining_table dm
  inner join gps_segments gs on gs.gps_segment_id = dm.gps_segment_id
"""

  cur = get_cursor()
  SQLExec(cur,sql);

  tot = cur.rowcount
  i=1
  for row in cur:
    if row['lateness'] is None:
      continue
    if i%1000 == 0:
      print i,"/",tot
    i+=1
    lateness_observed( row['gtfs_trip_id'], row['stop_id'],
                       row['dow'], 
                       row['stop_sequence'], row['lateness'],
                       auto_create = True );
  cur.close()


def get_routes_for_stop( stop_id ):
  sql = """\
select distinct(route_short_name) 
from gtf_routes gr 
  inner join gtf_trips gt 
    on gr.route_id = gt.route_id 
  inner join gtf_stop_times gst 
    on gst.trip_id = gt.trip_id 
where gst.stop_id = %(stopid)s
"""

  cur = get_cursor()
  SQLExec(cur,sql,{'stopid':stop_id})
  rows = cur.fetchall()
  cur.close()

  return [r[0] for r in rows]

